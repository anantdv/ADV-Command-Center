from __future__ import annotations

from app.schemas.metadata import FieldIntelligence
from app.services.metadata_service import MetadataService, metadata_service, normalize_field_text


class FieldResolver:
    def __init__(self, metadata: MetadataService | None = None) -> None:
        self.metadata = metadata or metadata_service

    async def resolve_field(self, doctype: str, phrase: str, cookies: dict | None = None) -> FieldIntelligence | None:
        intelligence = await self.metadata.get_doctype_intelligence(doctype, cookies)
        needle = normalize_field_text(phrase)
        for field in intelligence.fields:
            aliases = [field.fieldname, field.label, *field.aliases]
            if any(normalize_field_text(alias) == needle for alias in aliases):
                return field
        for field in intelligence.fields:
            if any(needle and needle in normalize_field_text(alias) for alias in [field.fieldname, field.label, *field.aliases]):
                return field
        return None


field_resolver = FieldResolver()

