from app.schemas.document_intake import DocumentMappingPreview, ExtractedDocumentFields
from app.utils.document_mapping_validator import validate_purchase_invoice_mapping


def test_purchase_invoice_requires_supplier_and_item_code():
    mapping = DocumentMappingPreview(
        intake_id="intake_1",
        source_document_type="supplier_invoice",
        target_doctype="Purchase Invoice",
        extracted_fields=ExtractedDocumentFields(source_document_type="supplier_invoice", target_doctype="Purchase Invoice"),
        draft_payload={"posting_date": "2026-07-16", "items": [{"description": "Fish", "qty": 1}]},
        confirmation_id="conf_1",
    )
    result = validate_purchase_invoice_mapping(mapping)
    assert result.valid is False
    assert result.confirmation_id is None
    assert {item["fieldname"] for item in result.missing_fields} == {"supplier", "items"}
