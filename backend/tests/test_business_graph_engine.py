import pytest

from app.schemas.business_graph import GraphEdgeType, GraphTraversalRequest, ReasoningRequest
from app.schemas.common import PermissionMeta
from app.schemas.erpnext import DocumentDetailResponse
from app.schemas.metadata import ChildTableIntelligence, DoctypeIntelligence, FieldIntelligence
from app.services.graph_builder import GraphBuilder
from app.services.graph_cache import GraphCache
from app.services.impact_analyzer import ImpactAnalyzer
from app.services.reasoning_engine import ReasoningEngine
from app.services.relationship_resolver import RelationshipResolver
from app.services.root_cause_engine import RootCauseEngine
from app.services.timeline_builder import TimelineBuilder
from app.services.traversal_engine import TraversalEngine


class FakeGraphERP:
    async def get_document_detail(self, doctype: str, name: str, cookies=None):
        records = {
            ("Purchase Order", "PUR-ORD-0001"): {
                "supplier": "SUPP-0001",
                "transaction_date": "2026-07-01",
                "status": "To Receive and Bill",
                "items": [
                    {"name": "ROW-1", "item_code": "ITEM-001", "qty": 2, "rate": 50, "amount": 100},
                    {"name": "ROW-2", "item_code": "ITEM-002", "qty": 1, "rate": 75, "amount": 75},
                ],
            },
            ("Supplier", "SUPP-0001"): {"supplier_name": "Acme Supplies", "modified": "2026-06-25", "status": "Enabled"},
            ("Item", "ITEM-001"): {"item_name": "Industrial Sensor", "modified": "2026-06-20", "status": "Enabled"},
            ("Item", "ITEM-002"): {"item_name": "Control Panel", "modified": "2026-06-22", "status": "Enabled"},
        }
        record = {"name": name, **records.get((doctype, name), {})}
        return DocumentDetailResponse(
            doctype=doctype,
            name=name,
            title=f"{doctype} {name}",
            status=record.get("status"),
            summary=record,
            fields=record,
            items=record.get("items") or [],
            permission=PermissionMeta(allowed=True, can_read=True).model_dump(),
        )


class FakeGraphMetadata:
    async def get_doctype_intelligence(self, doctype: str, cookies=None, refresh: bool = False):
        if doctype == "Purchase Order":
            supplier = FieldIntelligence(fieldname="supplier", label="Supplier", fieldtype="Link", options="Supplier", link_to="Supplier")
            item = FieldIntelligence(fieldname="item_code", label="Item", fieldtype="Link", options="Item", link_to="Item")
            return DoctypeIntelligence(
                doctype="Purchase Order",
                fields=[supplier],
                link_fields=[supplier],
                child_tables=[ChildTableIntelligence(fieldname="items", label="Items", child_doctype="Purchase Order Item", link_fields=[item])],
                permissions=PermissionMeta(allowed=True, can_read=True),
            )
        return DoctypeIntelligence(doctype=doctype, fields=[], permissions=PermissionMeta(allowed=True, can_read=True))


def _builder() -> GraphBuilder:
    return GraphBuilder(erp=FakeGraphERP(), metadata=FakeGraphMetadata(), resolver=RelationshipResolver(), cache=GraphCache())


@pytest.mark.asyncio
async def test_graph_builder_discovers_link_and_child_table_edges():
    graph = await _builder().neighborhood("Purchase Order", "PUR-ORD-0001", depth=1)

    assert graph.root.doctype == "Purchase Order"
    node_names = {(node.doctype, node.name) for node in graph.nodes}
    assert ("Supplier", "SUPP-0001") in node_names
    assert ("Purchase Order Item", "ROW-1") in node_names
    assert ("Item", "ITEM-001") in node_names
    assert any(edge.edge_type == GraphEdgeType.CONTAINS for edge in graph.edges)
    assert any(edge.fieldname == "supplier" for edge in graph.edges)
    assert any(edge.fieldname == "item_code" for edge in graph.edges)


@pytest.mark.asyncio
async def test_traversal_engine_finds_shortest_path_to_item():
    graph = await _builder().neighborhood("Purchase Order", "PUR-ORD-0001", depth=1)
    path = TraversalEngine().shortest_path(graph, "Item", "ITEM-001")

    assert path is not None
    assert path.nodes[0].doctype == "Purchase Order"
    assert path.nodes[-1].doctype == "Item"
    assert "Purchase Order" in path.explanation


@pytest.mark.asyncio
async def test_reasoning_engine_answers_impact_and_root_cause_from_graph():
    builder = _builder()
    engine = ReasoningEngine(builder=builder, traversal=TraversalEngine(), impact=ImpactAnalyzer(), root_cause=RootCauseEngine(), timeline=TimelineBuilder())

    impact = await engine.answer(ReasoningRequest(question="What is impacted if I cancel this?", doctype="Purchase Order", name="PUR-ORD-0001"))
    root = await engine.answer(ReasoningRequest(question="Why is this blocked?", doctype="Purchase Order", name="PUR-ORD-0001"))

    assert "may affect" in impact.answer
    assert "blocking" in root.answer.lower() or "No obvious blocking" in root.answer


@pytest.mark.asyncio
async def test_timeline_builder_sorts_related_events():
    graph = await _builder().neighborhood("Purchase Order", "PUR-ORD-0001", depth=2)
    timeline = TimelineBuilder().build(graph)

    dated = [event.event_date for event in timeline.events if event.event_date]
    assert dated == sorted(dated)
    assert any(event.doctype == "Purchase Order" for event in timeline.events)


def test_business_graph_api_contract(client):
    response = client.get("/api/business-graph/documents/Sales%20Invoice/SINV-2026-0418/related")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["doctype"] == "Sales Invoice"
    assert data["related"]["root"]["doctype"] == "Sales Invoice"


def test_business_graph_traverse_api_contract(client):
    response = client.post(
        "/api/business-graph/traverse",
        json=GraphTraversalRequest(doctype="Customer", name="CUST-0001", depth=1).model_dump(),
    )

    assert response.status_code == 200
    assert response.json()["data"]["root"]["name"] == "CUST-0001"
