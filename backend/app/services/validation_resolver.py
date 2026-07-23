from __future__ import annotations

from typing import Any

from app.services.metadata_service import MetadataService, metadata_service


class ValidationResolver:
    def __init__(self, metadata: MetadataService | None = None) -> None:
        self.metadata = metadata or metadata_service

    async def missing_required_fields(self, doctype: str, data: dict[str, Any], cookies: dict | None = None) -> list[str]:
        intelligence = await self.metadata.get_doctype_intelligence(doctype, cookies)
        missing = [field for field in intelligence.mandatory_fields if data.get(field) in (None, "", [])]
        for table in intelligence.child_tables:
            rows = data.get(table.fieldname)
            if table.required and (not isinstance(rows, list) or not rows):
                missing.append(table.fieldname)
        return list(dict.fromkeys(missing))

    async def writable_fields(self, doctype: str, cookies: dict | None = None) -> list[str]:
        intelligence = await self.metadata.get_doctype_intelligence(doctype, cookies)
        return intelligence.writable_fields


validation_resolver = ValidationResolver()

