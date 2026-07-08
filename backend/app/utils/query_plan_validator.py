from __future__ import annotations

import re
from typing import Any

from app.schemas.query_plan import QueryPlan
from app.utils.doctype_resolver import ALLOWED_QUERY_DOCTYPES
from app.utils.field_alias_mapper import get_default_fields
from app.utils.filter_normalizer import ALLOWED_FILTER_OPERATORS, normalize_filters

ALLOWED_REPORTS = {"Stock Balance", "Stock Ledger", "General Ledger", "Trial Balance", "Accounts Receivable", "Accounts Payable"}
SENSITIVE_FIELD_PATTERN = re.compile(r"(password|secret|token|api_key|api_secret|otp|salary|bank|account_no|pan|aadhaar|cookie|authorization|sid)", re.IGNORECASE)
SQL_PATTERN = re.compile(r"\b(select|insert|update|delete|drop|alter|truncate|union|from\s+tab)\b", re.IGNORECASE)


def validate_query_plan(plan: QueryPlan) -> QueryPlan:
    if _contains_sql(plan.filters) or _contains_sql(plan.data) or _contains_sql(plan.record_name or ""):
        plan.intent = "unsupported"
        plan.operation = "none"
        plan.blocked_reason = "SQL-like query content is not allowed."
        return plan

    plan.limit = min(max(int(plan.limit or 50), 1), 500)

    if plan.intent in {"list_records", "get_record", "generate_file", "pin_to_dashboard"}:
        if not plan.doctype and not plan.report_name:
            plan.intent = "unsupported"
            plan.operation = "none"
            plan.missing_information.append("doctype")
            return plan
        if plan.doctype and plan.doctype not in ALLOWED_QUERY_DOCTYPES:
            plan.intent = "unsupported"
            plan.operation = "none"
            plan.blocked_reason = f"Unsupported DocType: {plan.doctype}"
            return plan
    if plan.intent == "run_report" and plan.report_name and plan.report_name not in ALLOWED_REPORTS:
        plan.intent = "unsupported"
        plan.operation = "none"
        plan.blocked_reason = f"Unsupported report: {plan.report_name}"
        return plan

    if plan.doctype:
        plan.fields = _safe_fields(plan.fields or get_default_fields(plan.doctype))
        plan.normalized_filters = normalize_filters(plan.doctype, plan.filters, plan.date_range)
        plan.normalized_filters = _safe_filters(plan.normalized_filters)
    else:
        plan.fields = _safe_fields(plan.fields)
    return plan


def _safe_fields(fields: list[str]) -> list[str]:
    clean: list[str] = []
    for field in fields:
        if not field or SENSITIVE_FIELD_PATTERN.search(field):
            continue
        if field not in clean:
            clean.append(field)
    return clean or ["name"]


def _safe_filters(filters: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field, value in filters.items():
        if SENSITIVE_FIELD_PATTERN.search(str(field)):
            continue
        if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str):
            operator = value[0].lower()
            if operator not in ALLOWED_FILTER_OPERATORS:
                continue
        output[field] = value
    return output


def _contains_sql(value: Any) -> bool:
    if isinstance(value, str):
        return bool(SQL_PATTERN.search(value))
    if isinstance(value, dict):
        return any(_contains_sql(k) or _contains_sql(v) for k, v in value.items())
    if isinstance(value, (list, tuple)):
        return any(_contains_sql(item) for item in value)
    return False
