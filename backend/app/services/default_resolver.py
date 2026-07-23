from __future__ import annotations

from typing import Any

from app.services.metadata_service import MetadataService, metadata_service


class DefaultResolver:
    def __init__(self, metadata: MetadataService | None = None) -> None:
        self.metadata = metadata or metadata_service

    async def defaults_for(self, doctype: str, user_context: dict[str, Any] | None = None, cookies: dict | None = None) -> dict[str, Any]:
        intelligence = await self.metadata.get_doctype_intelligence(doctype, cookies)
        user_context = user_context or {}
        defaults: dict[str, Any] = {}
        for field in intelligence.fields:
            if field.default not in (None, ""):
                defaults[field.fieldname] = field.default
        if "company" in intelligence.writable_fields and user_context.get("company"):
            defaults.setdefault("company", user_context["company"])
        if "currency" in intelligence.writable_fields and user_context.get("company_currency"):
            defaults.setdefault("currency", user_context["company_currency"])
        return defaults


default_resolver = DefaultResolver()

