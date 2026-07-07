from __future__ import annotations

from typing import Any

from app.schemas.document_intake import DocumentMappingPreview, ExtractedDocumentFields
from app.services.crud_service import CrudService, crud_service


class DocumentMappingService:
    async def build_mapping_preview(self, intake_id: str, extracted: ExtractedDocumentFields, cookies: dict | None = None, user: str = "unknown") -> DocumentMappingPreview:
        target = extracted.target_doctype
        if not target:
            target = "Material Request"
        payload = self._payload(extracted, target)
        preview = await crud_service.prepare_create(target, payload, conversation_id=intake_id, message_id=None, cookies=cookies, user=user)
        return DocumentMappingPreview(
            intake_id=intake_id,
            source_document_type=extracted.source_document_type,
            target_doctype=target,
            extracted_fields=extracted,
            draft_payload=preview.data,
            missing_fields=[field.model_dump() for field in preview.missing_fields],
            warnings=[*extracted.warnings, *preview.warnings],
            confirmation_required=True,
            confirmation_id=preview.confirmation_id,
        )

    @staticmethod
    def _payload(extracted: ExtractedDocumentFields, target: str) -> dict[str, Any]:
        items = [item.model_dump(exclude_none=True) for item in extracted.items]
        common = {"currency": extracted.currency, "items": items}
        if target == "Purchase Invoice":
            return _clean({**common, "supplier": extracted.supplier, "bill_no": extracted.bill_no, "bill_date": extracted.bill_date, "posting_date": extracted.posting_date, "due_date": extracted.due_date})
        if target == "Sales Order":
            return _clean({**common, "customer": extracted.customer, "po_no": extracted.po_no, "po_date": extracted.po_date})
        if target == "Purchase Order":
            return _clean({**common, "supplier": extracted.supplier})
        if target == "Quotation":
            return _clean({**common, "quotation_to": "Customer", "party_name": extracted.customer})
        if target == "Delivery Note":
            return _clean({"customer": extracted.customer, "posting_date": extracted.posting_date, "items": items})
        if target == "Purchase Receipt":
            return _clean({"supplier": extracted.supplier, "posting_date": extracted.posting_date, "items": items})
        return _clean({"material_request_type": "Purchase", "items": items})


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in (None, "", [])}
