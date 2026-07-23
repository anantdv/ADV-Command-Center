from __future__ import annotations

from app.schemas.common import PermissionMeta
from app.services.metadata_service import MetadataService, metadata_service


class PermissionResolver:
    def __init__(self, metadata: MetadataService | None = None) -> None:
        self.metadata = metadata or metadata_service

    async def permissions_for(self, doctype: str, cookies: dict | None = None) -> PermissionMeta:
        intelligence = await self.metadata.get_doctype_intelligence(doctype, cookies)
        return intelligence.permissions


permission_resolver = PermissionResolver()

