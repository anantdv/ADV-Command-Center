from typing import Any

ALLOWED_CREATE_FIELDS = {
    "Customer": ["customer_name", "customer_type", "customer_group", "territory", "email_id", "mobile_no"],
    "Supplier": ["supplier_name", "supplier_type", "supplier_group", "country", "email_id", "mobile_no"],
    "Item": ["item_code", "item_name", "item_group", "stock_uom", "is_stock_item", "description"],
    "Lead": ["lead_name", "company_name", "email_id", "mobile_no", "status", "source"],
    "Opportunity": ["opportunity_from", "party_name", "opportunity_type", "opportunity_amount", "status", "transaction_date"],
    "Quotation": ["quotation_to", "party_name", "company", "transaction_date", "valid_till", "currency", "items"],
    "Sales Order": ["customer", "company", "transaction_date", "delivery_date", "currency", "po_no", "po_date", "items"],
    "Purchase Order": ["supplier", "company", "transaction_date", "schedule_date", "currency", "set_warehouse", "items"],
    "Sales Invoice": ["customer", "company", "posting_date", "due_date", "currency", "items"],
    "Purchase Invoice": ["supplier", "company", "bill_no", "bill_date", "posting_date", "due_date", "currency", "items"],
    "Delivery Note": ["customer", "company", "posting_date", "posting_time", "items"],
    "Purchase Receipt": ["supplier", "company", "posting_date", "posting_time", "items"],
    "Material Request": ["material_request_type", "company", "transaction_date", "schedule_date", "items"],
    "Stock Entry": ["stock_entry_type", "posting_date", "posting_time", "from_warehouse", "to_warehouse", "items"],
    "Journal Entry": ["voucher_type", "posting_date", "company", "accounts", "user_remark"],
    "Payment Entry": ["payment_type", "party_type", "party", "posting_date", "company", "paid_amount", "received_amount", "reference_no", "reference_date", "references"],
    "Expense Claim": ["employee", "posting_date", "company", "expenses", "remark"],
    "Leave Application": ["employee", "leave_type", "from_date", "to_date", "description"],
    "Employee": ["employee_name", "first_name", "last_name", "company", "gender", "date_of_birth", "date_of_joining"],
    "Asset": ["asset_name", "item_code", "company", "asset_category", "location", "gross_purchase_amount", "purchase_date"],
    "Work Order": ["production_item", "qty", "company", "bom_no", "planned_start_date", "fg_warehouse", "wip_warehouse"],
    "Job Card": ["work_order", "operation", "for_quantity", "employee", "posting_date"],
    "Issue": ["subject", "description", "priority", "issue_type", "customer", "status"],
    "Project": ["project_name", "status", "expected_start_date", "expected_end_date", "customer"],
    "Task": ["subject", "project", "status", "exp_start_date", "exp_end_date", "description"],
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
BLOCKED_WRITE_FIELDS = ["name", "owner", "creation", "modified", "modified_by", "idx", "amended_from", "submitted_by", "cancelled_by", "naming_series", "set_posting_time", "debit_to", "credit_to", "account", "base_paid_amount", "allocated_amount", "salary", "bank_account", "api_key", "api_secret", "password"]
REQUIRED_FIELDS = {
    "Customer": ["customer_name", "customer_group", "territory"],
    "Supplier": ["supplier_name", "supplier_group"],
    "Item": ["item_code", "item_name", "item_group", "stock_uom"],
    "Lead": ["lead_name"],
    "Opportunity": ["opportunity_from", "party_name"],
    "Quotation": ["quotation_to", "party_name", "items"],
    "Sales Order": ["customer", "items"],
    "Purchase Order": ["supplier", "items"],
    "Sales Invoice": ["customer", "items"],
    "Purchase Invoice": ["supplier", "items"],
    "Delivery Note": ["customer", "items"],
    "Purchase Receipt": ["supplier", "items"],
    "Material Request": ["material_request_type", "items"],
    "Stock Entry": ["stock_entry_type", "items"],
    "Journal Entry": ["accounts"],
    "Payment Entry": ["payment_type", "party_type", "party", "paid_amount"],
    "Expense Claim": ["employee", "expenses"],
    "Leave Application": ["employee", "leave_type", "from_date", "to_date"],
    "Employee": ["employee_name", "company"],
    "Asset": ["asset_name", "item_code", "company"],
    "Work Order": ["production_item", "qty"],
    "Job Card": ["work_order", "operation"],
    "Issue": ["subject", "description"],
    "Project": ["project_name"],
    "Task": ["subject"],
}
FIELD_LABELS = {field: field.replace("_", " ").title() for fields in [*ALLOWED_CREATE_FIELDS.values(), *ALLOWED_UPDATE_FIELDS.values()] for field in fields}
FIELD_OPTIONS = {"customer_type": "Individual\nCompany", "supplier_type": "Company\nIndividual", "quotation_to": "Customer\nLead", "opportunity_from": "Customer\nLead", "priority": "Low\nMedium\nHigh\nUrgent", "material_request_type": "Purchase\nMaterial Transfer\nMaterial Issue\nManufacture", "status": None}


def filter_write_data(doctype: str, operation: str, data: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    allowed = set((ALLOWED_CREATE_FIELDS if operation == "create" else ALLOWED_UPDATE_FIELDS).get(doctype, []))
    blocked = [field for field in data if field in BLOCKED_WRITE_FIELDS or field not in allowed]
    return {field:value for field,value in data.items() if field in allowed and field not in BLOCKED_WRITE_FIELDS}, blocked


def missing_required_fields(doctype: str, data: dict[str, Any]) -> list[str]:
    missing = [field for field in REQUIRED_FIELDS.get(doctype, []) if data.get(field) in (None, "", [])]
    if "items" in REQUIRED_FIELDS.get(doctype, []):
        rows = data.get("items") or []
        if not isinstance(rows, list) or not rows or any(isinstance(row, dict) and not row.get("item_code") for row in rows):
            if "items" not in missing:
                missing.append("items")
    return missing
