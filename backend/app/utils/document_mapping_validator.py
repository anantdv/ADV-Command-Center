from __future__ import annotations

from app.schemas.document_intake import DocumentMappingPreview


def validate_purchase_invoice_mapping(mapping: DocumentMappingPreview) -> DocumentMappingPreview:
    result = validate_purchase_invoice_payload(mapping.draft_payload)
    missing: list[dict] = []
    if "Supplier" in result["missing_fields"]:
        missing.append({"fieldname": "supplier", "label": "Supplier", "fieldtype": "Link", "options": "Supplier"})
    if "Posting Date" in result["missing_fields"]:
        missing.append({"fieldname": "posting_date", "label": "Posting Date", "fieldtype": "Date"})
    if "Items" in result["missing_fields"]:
        missing.append({"fieldname": "items", "label": "Items", "fieldtype": "Table"})
    mapping.missing_fields = _merge_missing(mapping.missing_fields, missing)
    mapping.blocking_errors = result["blocking_errors"]
    mapping.valid = bool(result["valid"]) and not mapping.missing_fields
    mapping.invalid_reason = None if mapping.valid else " ".join(mapping.blocking_errors) or "Please select Supplier and add at least one valid item before creating the draft."
    if not mapping.valid:
        mapping.confirmation_id = None
    return mapping


def validate_purchase_invoice_payload(payload: dict) -> dict:
    missing: list[str] = []
    errors: list[str] = []
    if not payload.get("supplier"):
        missing.append("Supplier")
        errors.append("Please select Supplier before creating the draft.")
    if not payload.get("posting_date"):
        missing.append("Posting Date")
        errors.append("Posting Date is required before creating the draft.")
    items = payload.get("items") or []
    valid_items = [item for item in items if item.get("item_code") and (item.get("qty") or 0) > 0]
    if not valid_items:
        missing.append("Items")
        errors.append("Please add at least one valid item.")
    return {"valid": not errors, "missing_fields": missing, "blocking_errors": errors}


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
    mapping.blocking_errors = []
    if not payload.get("customer"):
        mapping.blocking_errors.append("Please select Customer before creating the draft.")
    if not valid_items:
        mapping.blocking_errors.append("Please add at least one valid item.")
    mapping.valid = not mapping.missing_fields
    mapping.invalid_reason = None if mapping.valid else " ".join(mapping.blocking_errors) or "Please select Customer and add at least one valid item before creating the draft."
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
