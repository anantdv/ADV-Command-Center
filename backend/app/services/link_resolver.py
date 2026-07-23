from __future__ import annotations

from app.schemas.entity_resolution import EntitySearchContext, EntitySearchRequest, EntitySearchResponse
from app.services.entity_resolution_service import EntityResolutionService, entity_resolution_service
from app.services.field_resolver import FieldResolver, field_resolver


class LinkResolver:
    def __init__(self, entities: EntityResolutionService | None = None, fields: FieldResolver | None = None) -> None:
        self.entities = entities or entity_resolution_service
        self.fields = fields or field_resolver

    async def resolve_link_field(self, parent_doctype: str, fieldname_or_phrase: str, query: str, context: EntitySearchContext | None = None, cookies: dict | None = None) -> EntitySearchResponse:
        field = await self.fields.resolve_field(parent_doctype, fieldname_or_phrase, cookies)
        target = field.link_to if field and field.link_to else fieldname_or_phrase
        return await self.entities.search(EntitySearchRequest(doctype=target, query=query, context=context or EntitySearchContext(parent_doctype=parent_doctype)), cookies)


link_resolver = LinkResolver()

