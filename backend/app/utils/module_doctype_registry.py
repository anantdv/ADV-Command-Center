MODULE_DOCTYPE_REGISTRY = {
    "Selling": [
        {"doctype": "Customer", "label": "Customers", "description": "Customer master records and selling parties.", "icon": "users", "default_fields": ["name", "customer_name", "customer_group", "territory", "mobile_no", "email_id"], "search_fields": ["name", "customer_name", "mobile_no", "email_id"], "default_order_by": "modified desc"},
        {"doctype": "Lead", "label": "Leads", "description": "Potential customers and early sales prospects.", "icon": "user-plus", "default_fields": ["name", "lead_name", "company_name", "status", "email_id", "mobile_no", "creation"], "search_fields": ["name", "lead_name", "company_name", "email_id", "mobile_no"], "default_order_by": "modified desc"},
        {"doctype": "Opportunity", "label": "Opportunities", "description": "Sales opportunities and pipeline records.", "icon": "target", "default_fields": ["name", "opportunity_from", "party_name", "status", "opportunity_amount", "transaction_date"], "search_fields": ["name", "party_name"], "default_order_by": "modified desc"},
        {"doctype": "Quotation", "label": "Quotations", "description": "Customer quotations and estimates.", "icon": "file-text", "default_fields": ["name", "quotation_to", "party_name", "transaction_date", "valid_till", "grand_total", "status"], "search_fields": ["name", "party_name"], "default_order_by": "transaction_date desc"},
        {"doctype": "Sales Order", "label": "Sales Orders", "description": "Confirmed customer sales orders.", "icon": "shopping-cart", "default_fields": ["name", "customer", "transaction_date", "delivery_date", "grand_total", "status"], "search_fields": ["name", "customer"], "default_order_by": "transaction_date desc"},
        {"doctype": "Sales Invoice", "label": "Sales Invoices", "description": "Customer invoices and receivables.", "icon": "receipt", "default_fields": ["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"], "search_fields": ["name", "customer"], "default_order_by": "posting_date desc"},
        {"doctype": "Delivery Note", "label": "Delivery Notes", "description": "Customer delivery and dispatch documents.", "icon": "truck", "default_fields": ["name", "customer", "posting_date", "status", "grand_total", "docstatus"], "search_fields": ["name", "customer"], "default_order_by": "posting_date desc"},
        {"doctype": "Item", "label": "Items", "description": "Products and services available for selling.", "icon": "box", "default_fields": ["name", "item_code", "item_name", "item_group", "stock_uom", "disabled"], "search_fields": ["name", "item_code", "item_name"], "default_order_by": "modified desc"},
    ]
}


def module_doctypes(module_name: str) -> list[dict]:
    normalized = _normalize(module_name)
    return MODULE_DOCTYPE_REGISTRY.get(normalized, [])


def find_module_doctype(module_name: str, doctype: str) -> dict | None:
    return next((item for item in module_doctypes(module_name) if item["doctype"].lower() == doctype.lower()), None)


def _normalize(value: str) -> str:
    text = (value or "").strip().replace("-", " ").replace("_", " ").lower()
    return {"selling": "Selling", "accounts": "Accounts", "accounting": "Accounts", "buying": "Buying", "stock": "Stock"}.get(text, " ".join(part.capitalize() for part in text.split()))
