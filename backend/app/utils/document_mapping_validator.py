from __future__ import annotations

from app.schemas.document_intake import DocumentMappingPreview


def validate_purchase_invoice_mapping(mapping: DocumentMappingPreview) -> DocumentMappingPreview:
    payload = mapping.draft_payload
    missing: list[dict] = []
    if not payload.get("supplier"):
        missing.append({"fieldname": "supplier", "label": "Supplier", "fieldtype": "Link", "options": "Supplier"})
    if not payload.get("posting_date"):
        missing.append({"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Date"})
    items = payload.get("items") or []
    valid_items = [item for item in items if item.get("item_code") and (item.get("qty") or 0) > 0]
    if not valid_items:
        missing.append({"fieldname": "items", "label": "Items", "fieldtype": "Table"})
    mapping.missing_fields = _merge_missing(mapping.missing_fields, missing)
    mapping.valid = not mapping.missing_fields
    mapping.invalid_reason = None if mapping.valid else "Please select Supplier and add at least one valid item before creating the draft."
    if not mapping.valid:
        mapping.confirmation_id = None
    return mapping


def validate_sales_order_mapping(mapping: DocumentMappingPreview) -> DocumentMappingPreview:
    payload = mapping.draft_payload
    missing: list[dict] = []
    if not payload.get("customer"):
        missing.append({"fieldname": "customer", "label": "Customer", "fieldtype": "Link", "options": "Customer"})
    items = payload.get("items") or []
    valid_items = [item for item in items if item.get("item_code") and (item.get("qty") or 0) > 0]
    if not valid_items:
        missing.append({"fieldname": "items", "label": "Items", "fieldtype": "Table"})
    mapping.missing_fields = _merge_missing(mapping.missing_fields, missing)
    mapping.valid = not mapping.missing_fields
    mapping.invalid_reason = None if mapping.valid else "Please select Customer and add at least one valid item before creating the draft."
    if not mapping.valid:
        mapping.confirmation_id = None
    return mapping


def validate_mapping(mapping: DocumentMappingPreview) -> DocumentMappingPreview:
    if mapping.target_doctype == "Purchase Invoice":
        return validate_purchase_invoice_mapping(mapping)
    if mapping.target_doctype == "Sales Order":
        return validate_sales_order_mapping(mapping)
    mapping.valid = not mapping.missing_fields
    if not mapping.valid:
        mapping.confirmation_id = None
    return mapping


def _merge_missing(existing: list[dict], new: list[dict]) -> list[dict]:
    by_field = {str(item.get("fieldname")): item for item in existing}
    for item in new:
        by_field.setdefault(str(item.get("fieldname")), item)
    return list(by_field.values())
