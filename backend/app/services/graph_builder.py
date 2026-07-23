from __future__ import annotations

from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.business_graph import GraphEdge, GraphNeighborhood, GraphNode
from app.services.erpnext_service import ERPNextService
from app.services.graph_cache import GraphCache, graph_cache
from app.services.metadata_service import MetadataService, metadata_service
from app.services.relationship_resolver import RelationshipResolver, relationship_resolver


class GraphBuilder:
    def __init__(
        self,
        erp: ERPNextService | None = None,
        metadata: MetadataService | None = None,
        resolver: RelationshipResolver | None = None,
        cache: GraphCache | None = None,
    ) -> None:
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))
        self.metadata = metadata or metadata_service
        self.resolver = resolver or relationship_resolver
        self.cache = cache or graph_cache

    async def neighborhood(self, doctype: str, name: str, depth: int = 1, direction: str = "both", limit: int = 50, cookies: dict | None = None) -> GraphNeighborhood:
        cached = self.cache.get(doctype, name, depth, direction)
        if cached:
            return cached
        root_detail = await self.erp.get_document_detail(doctype, name, cookies)
        root_record = root_detail.fields or root_detail.summary or {"name": name}
        root = self.resolver.node(doctype, name, root_record)
        seen_nodes: dict[str, GraphNode] = {root.id: root}
        edges: list[GraphEdge] = []
        frontier = [(root, root_record, 0)]
        truncated = False
        while frontier and len(seen_nodes) < limit:
            node, record, current_depth = frontier.pop(0)
            if current_depth >= depth:
                continue
            try:
                intelligence = await self.metadata.get_doctype_intelligence(node.doctype, cookies)
            except Exception:
                continue
            neighbors, out_edges = self.resolver.outbound_edges(node, record, intelligence)
            for neighbor in neighbors:
                if len(seen_nodes) >= limit:
                    truncated = True
                    break
                if neighbor.id not in seen_nodes:
                    seen_nodes[neighbor.id] = neighbor
                    if current_depth + 1 < depth and neighbor.node_type.value != "child_row":
                        try:
                            detail = await self.erp.get_document_detail(neighbor.doctype, neighbor.name, cookies)
                            frontier.append((neighbor, detail.fields or detail.summary or {"name": neighbor.name}, current_depth + 1))
                        except Exception:
                            pass
            edges.extend(edge for edge in out_edges if edge.source_id in seen_nodes and edge.target_id in seen_nodes)
        graph = GraphNeighborhood(root=root, nodes=list(seen_nodes.values()), edges=edges[:limit], depth=depth, truncated=truncated)
        self.cache.set(doctype, name, depth, direction, graph)
        return graph


graph_builder = GraphBuilder()

