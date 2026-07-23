from __future__ import annotations

from app.schemas.business_graph import RelatedDocumentsResponse
from app.services.graph_builder import GraphBuilder, graph_builder


class RelatedDocumentResolver:
    def __init__(self, builder: GraphBuilder | None = None) -> None:
        self.builder = builder or graph_builder

    async def related(self, doctype: str, name: str, depth: int = 1, cookies: dict | None = None) -> RelatedDocumentsResponse:
        graph = await self.builder.neighborhood(doctype, name, depth=depth, cookies=cookies)
        return RelatedDocumentsResponse(doctype=doctype, name=name, related=graph)


related_document_resolver = RelatedDocumentResolver()

