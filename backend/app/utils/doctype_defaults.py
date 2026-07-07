from __future__ import annotations

from datetime import date
from typing import Any


DATE_DEFAULTS = {
    "Quotation": ("transaction_date",),
    "Sales Order": ("transaction_date",),
    "Purchase Order": ("transaction_date",),
    "Sales Invoice": ("posting_date",),
    "Purchase Invoice": ("posting_date", "bill_date"),
    "Delivery Note": ("posting_date",),
    "Purchase Receipt": ("posting_date",),
    "Material Request": ("transaction_date",),
    "Opportunity": ("transaction_date",),
    "Project": ("expected_start_date",),
    "Task": ("exp_start_date",),
}


def apply_document_defaults(doctype: str, data: dict[str, Any], user_context: dict | None = None) -> dict[str, Any]:
    """Apply safe draft-only defaults and leave accounting/tax defaults to ERPNext."""
    output = dict(data)
    today = date.today().isoformat()
    for field in DATE_DEFAULTS.get(doctype, ()):
        output.setdefault(field, today)
    if doctype in {"Sales Order", "Purchase Order", "Material Request"}:
        if "schedule_date" in output or doctype in {"Purchase Order", "Material Request"}:
            output.setdefault("schedule_date", today)
    if doctype in {"Sales Order", "Delivery Note", "Task", "Project"}:
        if doctype == "Sales Order":
            output.setdefault("delivery_date", today)
        if doctype == "Task":
            output.setdefault("exp_end_date", output.get("exp_start_date", today))
    currency = (user_context or {}).get("currency") or (user_context or {}).get("default_currency")
    if currency and doctype in {"Quotation", "Sales Order", "Purchase Order", "Sales Invoice", "Purchase Invoice"}:
        output.setdefault("currency", currency)
    output["docstatus"] = 0
    return output
