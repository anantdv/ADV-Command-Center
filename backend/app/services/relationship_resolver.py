from __future__ import annotations

import hashlib
from typing import Any

from app.schemas.business_graph import GraphEdge, GraphEdgeType, GraphNode, GraphNodeType
from app.schemas.metadata import DoctypeIntelligence
from app.utils.ids import new_id


TRANSACTION_HINTS = {"Invoice", "Order", "Receipt", "Entry", "Note", "Request", "Claim", "Application", "Work Order", "Production Plan"}
MASTER_HINTS = {"Customer", "Supplier", "Item", "Warehouse", "Employee", "Project", "Asset", "Company", "Account", "Currency"}


class RelationshipResolver:
    """Discovers graph relationships from metadata and document data."""

    def node_id(self, doctype: str, name: str) -> str:
        digest = hashlib.sha1(f"{doctype}:{name}".encode()).hexdigest()[:16]
        return f"node_{digest}"

    def node(self, doctype: str, name: str, record: dict[str, Any] | None = None) -> GraphNode:
        record = record or {}
        label = str(record.get("title") or record.get("customer_name") or record.get("supplier_name") or record.get("item_name") or record.get("subject") or name)
        return GraphNode(id=self.node_id(doctype, name), doctype=doctype, name=name, label=label, node_type=self._node_type(doctype), status=record.get("status") or record.get("workflow_state"), metadata={key: record.get(key) for key in ("docstatus", "posting_date", "transaction_date", "creation", "modified") if key in record})

    def outbound_edges(self, source: GraphNode, record: dict[str, Any], metadata: DoctypeIntelligence) -> tuple[list[GraphNode], list[GraphEdge]]:
        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        for field in metadata.link_fields:
            target_name = record.get(field.fieldname)
            if target_name in (None, "", []):
                continue
            target_doctype = field.link_to or str(field.options or "")
            target = self.node(target_doctype, str(target_name))
            nodes.append(target)
            edges.append(self.edge(source, target, GraphEdgeType.LINKS_TO, f"{metadata.doctype}.{field.fieldname}", field.fieldname))
        for table in metadata.child_tables:
            rows = record.get(table.fieldname) or []
            if not isinstance(rows, list):
                continue
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                child_name = str(row.get("name") or f"{source.name}:{table.fieldname}:{index+1}")
                child = self.node(table.child_doctype, child_name, row)
                child.node_type = GraphNodeType.CHILD_ROW
                nodes.append(child)
                edges.append(self.edge(source, child, GraphEdgeType.CONTAINS, table.label, table.fieldname, {"row_index": index}))
                for link in table.link_fields:
                    linked_name = row.get(link.fieldname)
                    if linked_name in (None, "", []):
                        continue
                    linked = self.node(link.link_to or str(link.options or ""), str(linked_name))
                    nodes.append(linked)
                    edges.append(self.edge(child, linked, GraphEdgeType.LINKS_TO, f"{table.child_doctype}.{link.fieldname}", link.fieldname))
        return nodes, edges

    def inferred_business_edge(self, source: GraphNode, target: GraphNode, fieldname: str | None = None) -> GraphEdgeType:
        pair = (source.doctype, target.doctype)
        if "Payment Entry" in pair:
            return GraphEdgeType.PAID_BY
        if "GL Entry" in pair:
            return GraphEdgeType.POSTED_TO
        if "Task" in pair and target.doctype in {"Employee", "User"}:
            return GraphEdgeType.ASSIGNED_TO
        if fieldname in {"project", "parent_project"}:
            return GraphEdgeType.CONTAINS
        return GraphEdgeType.RELATED_TO

    def edge(self, source: GraphNode, target: GraphNode, edge_type: GraphEdgeType, label: str, fieldname: str | None = None, metadata: dict[str, Any] | None = None) -> GraphEdge:
        if edge_type == GraphEdgeType.LINKS_TO:
            edge_type = self.inferred_business_edge(source, target, fieldname)
        return GraphEdge(id=new_id("edge"), source_id=source.id, target_id=target.id, edge_type=edge_type, label=label, fieldname=fieldname, metadata=metadata or {})

    @staticmethod
    def _node_type(doctype: str) -> GraphNodeType:
        if doctype in MASTER_HINTS:
            return GraphNodeType.MASTER
        if any(hint in doctype for hint in TRANSACTION_HINTS):
            return GraphNodeType.TRANSACTION
        return GraphNodeType.DOCUMENT


relationship_resolver = RelationshipResolver()

