from __future__ import annotations

from typing import Any

from app.schemas.document_intake import DocumentMappingPreview, ExtractedDocumentFields, FieldExtraction
from app.services.crud_service import CrudService, crud_service
from app.utils.document_mapping_validator import validate_mapping
from app.utils.ocr_item_matcher import OcrItemMatcher
from app.utils.ocr_party_matcher import OcrPartyMatcher


class DocumentMappingService:
    def __init__(self) -> None:
        self.party_matcher = OcrPartyMatcher()
        self.item_matcher = OcrItemMatcher()

    async def build_mapping_preview(self, intake_id: str, extracted: ExtractedDocumentFields, cookies: dict | None = None, user: str = "unknown", raw_text_preview: str | None = None) -> DocumentMappingPreview:
        target = extracted.target_doctype
        if not target:
            target = "Material Request"
        payload = self._payload(extracted, target)
        field_extractions = await self._field_extractions(target, extracted, raw_text_preview or "", cookies)
        payload = self._apply_selected_matches(payload, field_extractions)
        preview = await crud_service.prepare_create(target, payload, conversation_id=intake_id, message_id=None, cookies=cookies, user=user)
        mapping = DocumentMappingPreview(
            intake_id=intake_id,
            source_document_type=extracted.source_document_type,
            target_doctype=target,
            extracted_fields=extracted,
            field_extractions=field_extractions,
            draft_payload=preview.data,
            missing_fields=[field.model_dump() for field in preview.missing_fields],
            warnings=[*extracted.warnings, *preview.warnings],
            raw_text_preview=raw_text_preview,
            confidence=self._confidence(field_extractions),
            confirmation_required=True,
            confirmation_id=preview.confirmation_id,
        )
        return validate_mapping(mapping)

    async def rebuild_from_edited_payload(self, intake_id: str, source_type: str, target: str, payload: dict[str, Any], cookies: dict | None = None, user: str = "unknown", raw_text_preview: str | None = None, warnings: list[str] | None = None) -> DocumentMappingPreview:
        extracted = ExtractedDocumentFields(source_document_type=source_type, target_doctype=target, supplier=payload.get("supplier"), customer=payload.get("customer"), bill_no=payload.get("bill_no"), bill_date=payload.get("bill_date"), po_no=payload.get("po_no"), po_date=payload.get("po_date"), posting_date=payload.get("posting_date"), due_date=payload.get("due_date"), currency=payload.get("currency"), grand_total=payload.get("grand_total"), tax_amount=payload.get("tax_amount"), items=payload.get("items") or [], warnings=warnings or [])
        preview = await crud_service.prepare_create(target, payload, conversation_id=intake_id, message_id=None, cookies=cookies, user=user)
        mapping = DocumentMappingPreview(
            intake_id=intake_id,
            source_document_type=source_type,
            target_doctype=target,
            extracted_fields=extracted,
            draft_payload=preview.data,
            missing_fields=[field.model_dump() for field in preview.missing_fields],
            warnings=[*(warnings or []), *preview.warnings],
            raw_text_preview=raw_text_preview,
            confirmation_required=True,
            confirmation_id=preview.confirmation_id,
        )
        return validate_mapping(mapping)

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

    async def _field_extractions(self, target: str, extracted: ExtractedDocumentFields, raw_text: str, cookies: dict | None) -> list[FieldExtraction]:
        output: list[FieldExtraction] = []
        if target == "Purchase Invoice":
            supplier_match = await self.party_matcher.match_supplier(raw_text, extracted.supplier, cookies)
            output.append(FieldExtraction(fieldname="supplier", label="Supplier", value=extracted.supplier, confidence=0.9 if supplier_match.get("matched") else 0.25, candidates=supplier_match.get("candidates") or [], required=True, warning=supplier_match.get("warning")))
            output.extend([
                FieldExtraction(fieldname="bill_no", label="Bill No", value=extracted.bill_no, confidence=0.82 if extracted.bill_no else 0.0, warning=None if extracted.bill_no else "Could not confidently extract invoice number."),
                FieldExtraction(fieldname="bill_date", label="Bill Date", value=extracted.bill_date, confidence=0.82 if extracted.bill_date else 0.0, warning=None if extracted.bill_date else "Could not confidently extract invoice date."),
                FieldExtraction(fieldname="posting_date", label="Posting Date", value=extracted.posting_date, confidence=0.7 if extracted.posting_date else 0.0, required=True),
            ])
        elif target == "Sales Order":
            customer_match = await self.party_matcher.match_customer(raw_text, extracted.customer, cookies)
            output.append(FieldExtraction(fieldname="customer", label="Customer", value=extracted.customer, confidence=0.9 if customer_match.get("matched") else 0.25, candidates=customer_match.get("candidates") or [], required=True, warning=customer_match.get("warning")))
        item_matches = await self.item_matcher.match_items(extracted.items, cookies)
        for index, match in enumerate(item_matches):
            if index < len(extracted.items):
                extracted.items[index].candidates = match.get("candidates") or []
                selected = match.get("selected")
                if selected and not extracted.items[index].item_code:
                    extracted.items[index].item_code = selected.get("name")
        return output

    @staticmethod
    def _apply_selected_matches(payload: dict[str, Any], fields: list[FieldExtraction]) -> dict[str, Any]:
        data = dict(payload)
        for field in fields:
            selected = field.candidates[0] if field.candidates and field.candidates[0].get("score", 0) >= 0.86 else None
            if selected and field.fieldname in {"supplier", "customer"}:
                data[field.fieldname] = selected.get("name")
        return data

    @staticmethod
    def _confidence(fields: list[FieldExtraction]) -> float | None:
        if not fields:
            return None
        return round(sum(field.confidence for field in fields) / len(fields), 2)


def _clean(data: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in data.items() if value not in (None, "", [])}
