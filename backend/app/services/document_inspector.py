from __future__ import annotations

from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.metadata import DocumentInspectionResponse
from app.services.erpnext_service import ERPNextService
from app.services.metadata_service import MetadataService, metadata_service
from app.services.validation_resolver import ValidationResolver, validation_resolver


class DocumentInspector:
    def __init__(
        self,
        metadata: MetadataService | None = None,
        validator: ValidationResolver | None = None,
        erp: ERPNextService | None = None,
    ) -> None:
        self.metadata = metadata or metadata_service
        self.validator = validator or validation_resolver
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))

    async def inspect(self, doctype: str, name: str | None = None, data: dict[str, Any] | None = None, cookies: dict | None = None) -> DocumentInspectionResponse:
        intelligence = await self.metadata.get_doctype_intelligence(doctype, cookies)
        record = data or {}
        workflow_state = None
        actions: list[dict[str, Any]] = []
        if name:
            detail = await self.erp.get_document_detail(doctype, name, cookies)
            record = detail.fields or detail.summary or {}
            workflow_state = detail.workflow_state
            actions = detail.available_workflow_actions
        missing = await self.validator.missing_required_fields(doctype, record, cookies)
        links = [
            {"fieldname": field.fieldname, "label": field.label, "link_to": field.link_to, "value": record.get(field.fieldname)}
            for field in intelligence.link_fields
            if field.fieldname in record or not name
        ]
        return DocumentInspectionResponse(doctype=doctype, name=name, metadata=intelligence, missing_required_fields=missing, workflow_state=workflow_state, available_actions=actions, links=links)


document_inspector = DocumentInspector()

