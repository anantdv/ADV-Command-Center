from __future__ import annotations

from app.schemas.metadata import WorkflowIntelligence
from app.services.metadata_service import MetadataService, metadata_service


class WorkflowResolver:
    def __init__(self, metadata: MetadataService | None = None) -> None:
        self.metadata = metadata or metadata_service

    async def workflow_for(self, doctype: str, cookies: dict | None = None) -> WorkflowIntelligence:
        intelligence = await self.metadata.get_doctype_intelligence(doctype, cookies)
        return intelligence.workflow


workflow_resolver = WorkflowResolver()

