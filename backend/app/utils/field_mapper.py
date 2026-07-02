from typing import Any

ALLOWED_CREATE_FIELDS = {
    "Customer": ["customer_name", "customer_type", "customer_group", "territory", "email_id", "mobile_no"],
    "Supplier": ["supplier_name", "supplier_type", "supplier_group", "country", "email_id", "mobile_no"],
    "Item": ["item_code", "item_name", "item_group", "stock_uom", "is_stock_item", "description"],
    "Quotation": ["quotation_to", "party_name", "transaction_date", "valid_till", "items"],
    "Lead": ["lead_name", "company_name", "email_id", "mobile_no", "status", "source"],
    "Opportunity": ["opportunity_from", "party_name", "opportunity_type", "opportunity_amount", "status", "transaction_date"],
    "Issue": ["subject", "description", "priority", "issue_type", "customer", "status"],
}
ALLOWED_UPDATE_FIELDS = {
    "Customer": ["customer_name", "customer_type", "customer_group", "territory", "email_id", "mobile_no", "disabled"],
    "Supplier": ["supplier_name", "supplier_type", "supplier_group", "country", "email_id", "mobile_no", "disabled"],
    "Item": ["item_name", "item_group", "stock_uom", "description", "disabled"],
    "Lead": ["lead_name", "company_name", "email_id", "mobile_no", "status", "source"],
    "Opportunity": ["opportunity_type", "opportunity_amount", "status"],
    "Issue": ["subject", "description", "priority", "status"],
    "Quotation": ["valid_till", "items"],
}
BLOCKED_WRITE_FIELDS = ["name", "owner", "creation", "modified", "modified_by", "docstatus", "idx", "amended_from", "submitted_by", "cancelled_by", "naming_series", "company", "posting_date", "posting_time", "set_posting_time", "debit_to", "credit_to", "account", "paid_amount", "base_paid_amount", "allocated_amount", "salary", "bank_account", "api_key", "api_secret", "password"]
REQUIRED_FIELDS = {
    "Customer": ["customer_name", "customer_group", "territory"],
    "Supplier": ["supplier_name", "supplier_group"],
    "Item": ["item_code", "item_name", "item_group", "stock_uom"],
    "Quotation": ["quotation_to", "party_name", "items"],
    "Lead": ["lead_name"],
    "Opportunity": ["opportunity_from", "party_name"],
    "Issue": ["subject", "description"],
}
FIELD_LABELS = {field: field.replace("_", " ").title() for fields in [*ALLOWED_CREATE_FIELDS.values(), *ALLOWED_UPDATE_FIELDS.values()] for field in fields}
FIELD_OPTIONS = {"customer_type": "Individual\nCompany", "quotation_to": "Customer\nLead", "opportunity_from": "Customer\nLead", "priority": "Low\nMedium\nHigh", "status": None}


def filter_write_data(doctype: str, operation: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    allowed = set((ALLOWED_CREATE_FIELDS if operation == "create" else ALLOWED_UPDATE_FIELDS).get(doctype, []))
    blocked = [field for field in data if field in BLOCKED_WRITE_FIELDS or field not in allowed]
    return {field:value for field,value in data.items() if field in allowed and field not in BLOCKED_WRITE_FIELDS}, blocked


def missing_required_fields(doctype: str, data: dict[str, Any]) -> list[str]:
    return [field for field in REQUIRED_FIELDS.get(doctype, []) if data.get(field) in (None, "", [])]
