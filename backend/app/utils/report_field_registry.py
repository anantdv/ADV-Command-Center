from __future__ import annotations

from typing import Any


SENSITIVE_FIELD_KEYWORDS = (
    "password", "secret", "api_key", "api_secret", "token", "otp", "salary", "bank",
    "account_no", "pan", "aadhaar", "authorization", "cookie", "sid",
)


REPORT_FIELDS: dict[str, dict[str, list[str]]] = {
    "Customer": {
        "detail_fields": ["name", "customer_name", "customer_group", "territory", "customer_type", "mobile_no", "email_id", "disabled", "creation"],
        "groupable_fields": ["customer_group", "territory", "customer_type", "disabled"],
        "numeric_fields": [],
        "date_fields": ["creation"],
        "blocked_fields": ["owner", "modified_by"],
    },
    "Supplier": {
        "detail_fields": ["name", "supplier_name", "supplier_group", "country", "supplier_type", "mobile_no", "email_id", "disabled", "creation"],
        "groupable_fields": ["supplier_group", "country", "supplier_type", "disabled"],
        "numeric_fields": [],
        "date_fields": ["creation"],
        "blocked_fields": ["owner", "modified_by"],
    },
    "Item": {
        "detail_fields": ["name", "item_code", "item_name", "item_group", "stock_uom", "disabled", "creation"],
        "groupable_fields": ["item_group", "stock_uom", "disabled"],
        "numeric_fields": [],
        "date_fields": ["creation"],
        "blocked_fields": ["owner", "modified_by"],
    },
    "Sales Invoice": {
        "detail_fields": ["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status", "currency", "docstatus"],
        "groupable_fields": ["customer", "status", "currency", "docstatus"],
        "numeric_fields": ["grand_total", "outstanding_amount", "base_grand_total"],
        "date_fields": ["posting_date", "due_date", "creation"],
        "blocked_fields": ["debit_to", "party_account_currency"],
    },
    "Purchase Invoice": {
        "detail_fields": ["name", "supplier", "posting_date", "bill_no", "bill_date", "due_date", "grand_total", "outstanding_amount", "status", "currency", "docstatus"],
        "groupable_fields": ["supplier", "status", "currency", "docstatus"],
        "numeric_fields": ["grand_total", "outstanding_amount", "base_grand_total"],
        "date_fields": ["posting_date", "bill_date", "due_date", "creation"],
        "blocked_fields": ["credit_to", "party_account_currency"],
    },
    "Sales Order": {
        "detail_fields": ["name", "customer", "transaction_date", "delivery_date", "grand_total", "status", "currency", "docstatus"],
        "groupable_fields": ["customer", "status", "currency", "docstatus"],
        "numeric_fields": ["grand_total", "base_grand_total"],
        "date_fields": ["transaction_date", "delivery_date", "creation"],
        "blocked_fields": [],
    },
    "Purchase Order": {
        "detail_fields": ["name", "supplier", "transaction_date", "schedule_date", "grand_total", "status", "currency", "docstatus"],
        "groupable_fields": ["supplier", "status", "currency", "docstatus"],
        "numeric_fields": ["grand_total", "base_grand_total"],
        "date_fields": ["transaction_date", "schedule_date", "creation"],
        "blocked_fields": [],
    },
    "Quotation": {
        "detail_fields": ["name", "quotation_to", "party_name", "transaction_date", "valid_till", "grand_total", "status", "currency", "docstatus"],
        "groupable_fields": ["quotation_to", "party_name", "status", "currency", "docstatus"],
        "numeric_fields": ["grand_total", "base_grand_total"],
        "date_fields": ["transaction_date", "valid_till", "creation"],
        "blocked_fields": [],
    },
    "Delivery Note": {
        "detail_fields": ["name", "customer", "posting_date", "status", "docstatus", "grand_total", "currency"],
        "groupable_fields": ["customer", "status", "docstatus", "currency"],
        "numeric_fields": ["grand_total", "base_grand_total"],
        "date_fields": ["posting_date", "creation"],
        "blocked_fields": [],
    },
    "Purchase Receipt": {
        "detail_fields": ["name", "supplier", "posting_date", "status", "docstatus", "grand_total", "currency"],
        "groupable_fields": ["supplier", "status", "docstatus", "currency"],
        "numeric_fields": ["grand_total", "base_grand_total"],
        "date_fields": ["posting_date", "creation"],
        "blocked_fields": [],
    },
    "Material Request": {
        "detail_fields": ["name", "material_request_type", "transaction_date", "schedule_date", "status", "docstatus"],
        "groupable_fields": ["material_request_type", "status", "docstatus"],
        "numeric_fields": [],
        "date_fields": ["transaction_date", "schedule_date", "creation"],
        "blocked_fields": [],
    },
    "Issue": {
        "detail_fields": ["name", "subject", "status", "priority", "issue_type", "creation"],
        "groupable_fields": ["status", "priority", "issue_type"],
        "numeric_fields": [],
        "date_fields": ["creation"],
        "blocked_fields": [],
    },
}


FIELD_ALIASES = {
    "customer": "customer",
    "supplier": "supplier",
    "invoice count": "name",
    "document count": "name",
    "count": "name",
    "total amount": "grand_total",
    "total": "grand_total",
    "value": "grand_total",
    "sales total": "grand_total",
    "purchase total": "grand_total",
    "outstanding": "outstanding_amount",
    "outstanding amount": "outstanding_amount",
    "status": "status",
    "date": "posting_date",
    "month": "period",
    "item group": "item_group",
}


def get_allowed_detail_fields(source_name: str) -> list[str]:
    return list(REPORT_FIELDS.get(source_name, {}).get("detail_fields", ["name"]))


def get_groupable_fields(source_name: str) -> list[str]:
    return list(REPORT_FIELDS.get(source_name, {}).get("groupable_fields", []))


def get_numeric_fields(source_name: str) -> list[str]:
    return list(REPORT_FIELDS.get(source_name, {}).get("numeric_fields", []))


def get_date_fields(source_name: str) -> list[str]:
    return list(REPORT_FIELDS.get(source_name, {}).get("date_fields", []))


def blocked_fields(source_name: str) -> set[str]:
    return set(REPORT_FIELDS.get(source_name, {}).get("blocked_fields", []))


def is_sensitive_field(fieldname: str) -> bool:
    lowered = fieldname.lower()
    return any(keyword in lowered for keyword in SENSITIVE_FIELD_KEYWORDS)


def resolve_field_alias(source_name: str, value: str) -> str:
    field = FIELD_ALIASES.get(value.strip().lower(), value.strip())
    if field == "posting_date" and "posting_date" not in get_allowed_detail_fields(source_name):
        if "transaction_date" in get_allowed_detail_fields(source_name):
            return "transaction_date"
    return field


def validate_fields(source_name: str, fields: list[str]) -> list[str]:
    allowed = set(get_allowed_detail_fields(source_name))
    blocked = blocked_fields(source_name)
    output: list[str] = []
    for raw in fields:
        field = resolve_field_alias(source_name, raw)
        if field in allowed and field not in blocked and not is_sensitive_field(field):
            output.append(field)
    return list(dict.fromkeys(output))


def validate_group_by(source_name: str, group_by: list[str]) -> list[str]:
    allowed = set(get_groupable_fields(source_name))
    return list(dict.fromkeys(field for field in (resolve_field_alias(source_name, item) for item in group_by) if field in allowed and not is_sensitive_field(field)))


def validate_metrics(source_name: str, metrics: list[dict[str, Any]]) -> list[dict[str, Any]]:
    numeric = set(get_numeric_fields(source_name))
    output: list[dict[str, Any]] = []
    for metric in metrics:
        field = resolve_field_alias(source_name, str(metric.get("fieldname") or metric.get("field") or "name"))
        function = str(metric.get("function") or "count").lower()
        if function == "count" and field == "name":
            output.append({**metric, "fieldname": "name", "function": "count"})
        elif function in {"sum", "avg", "min", "max"} and field in numeric:
            output.append({**metric, "fieldname": field, "function": function})
    return output
