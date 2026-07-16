from app.schemas.document_intake import DocumentMappingPreview, ExtractedDocumentFields
from app.utils.document_mapping_validator import validate_purchase_invoice_mapping


def _mapping(payload):
    return DocumentMappingPreview(
        intake_id="intake_1",
        source_document_type="supplier_invoice",
        target_doctype="Purchase Invoice",
        extracted_fields=ExtractedDocumentFields(source_document_type="supplier_invoice", target_doctype="Purchase Invoice"),
        draft_payload=payload,
        confirmation_id="conf_1",
    )


def test_missing_items_disables_confirmation():
    mapping = validate_purchase_invoice_mapping(_mapping({"supplier": "SUPP-0001", "posting_date": "2026-07-16"}))
    assert mapping.valid is False
    assert mapping.confirmation_id is None


def test_edited_mapping_with_supplier_and_item_is_valid():
    mapping = validate_purchase_invoice_mapping(_mapping({"supplier": "SUPP-0001", "posting_date": "2026-07-16", "items": [{"item_code": "ITEM-001", "qty": 1, "rate": 10}]}))
    assert mapping.valid is True
    assert mapping.confirmation_id == "conf_1"
