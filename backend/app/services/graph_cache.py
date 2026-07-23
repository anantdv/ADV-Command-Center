from __future__ import annotations

from app.schemas.business_graph import GraphNeighborhood
from app.services.schema_cache import SchemaCache


class GraphCache:
    def __init__(self, ttl_seconds: int = 300) -> None:
        self.cache = SchemaCache(ttl_seconds)

    def key(self, doctype: str, name: str, depth: int, direction: str) -> str:
        return f"graph:{doctype}:{name}:{depth}:{direction}"

    def get(self, doctype: str, name: str, depth: int, direction: str) -> GraphNeighborhood | None:
        return self.cache.get(self.key(doctype, name, depth, direction))

    def set(self, doctype: str, name: str, depth: int, direction: str, value: GraphNeighborhood) -> None:
        self.cache.set(self.key(doctype, name, depth, direction), value)

    def invalidate_document(self, doctype: str, name: str) -> None:
        # Coarse invalidation for now; SQL-backed graph indexes can invalidate
        # exact neighbor caches when document-change hooks are added.
        self.cache.invalidate()


graph_cache = GraphCache()

