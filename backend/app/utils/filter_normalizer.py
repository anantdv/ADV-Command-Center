from __future__ import annotations

from typing import Any

from app.utils.field_alias_mapper import map_field_alias

ALLOWED_FILTER_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "in", "not in", "like", "between"}

DOCTYPE_DATE_FIELD = {
    "Sales Invoice": "posting_date",
    "Purchase Invoice": "posting_date",
    "Sales Order": "transaction_date",
    "Purchase Order": "transaction_date",
    "Quotation": "transaction_date",
    "Delivery Note": "posting_date",
    "Purchase Receipt": "posting_date",
    "Material Request": "transaction_date",
    "Lead": "creation",
    "Opportunity": "transaction_date",
    "Issue": "creation",
}

STATUS_ALIASES = {
    "Sales Invoice": {"unpaid": ["in", ["Unpaid", "Overdue"]], "paid": "Paid", "overdue": "Overdue", "draft": "Draft", "cancelled": "Cancelled"},
    "Purchase Invoice": {"unpaid": ["in", ["Unpaid", "Overdue"]], "paid": "Paid", "overdue": "Overdue", "draft": "Draft", "cancelled": "Cancelled"},
    "Sales Order": {"open": ["in", ["To Deliver and Bill", "To Bill", "To Deliver"]], "completed": "Completed", "closed": "Closed", "draft": "Draft", "cancelled": "Cancelled"},
    "Purchase Order": {"open": ["in", ["To Receive and Bill", "To Bill", "To Receive"]], "completed": "Completed", "closed": "Closed", "draft": "Draft", "cancelled": "Cancelled"},
}


class FilterNormalizationError(Exception):
    pass


def normalize_filters(doctype: str, raw_filters: dict[str, Any] | list[Any] | None, date_range: dict[str, Any] | None = None) -> dict[str, Any]:
    output: dict[str, Any] = {}
    if isinstance(raw_filters, list):
        raw_filters = _list_to_dict(raw_filters)
    for raw_field, raw_value in (raw_filters or {}).items():
        field = map_field_alias(doctype, str(raw_field))
        if str(raw_field) == "month" and isinstance(raw_value, str):
            continue
        output[field] = _normalize_value(doctype, field, raw_value)
    if date_range:
        date_field = DOCTYPE_DATE_FIELD.get(doctype)
        if date_field and date_range.get("from_date") and date_range.get("to_date"):
            output[date_field] = ["between", [date_range["from_date"], date_range["to_date"]]]
    return output


def to_frappe_filters(doctype: str, filters: dict[str, Any], style: str = "list") -> dict[str, Any] | list[list[Any]]:
    """Convert normalized filters to Frappe's explicit list-of-lists format.

    This avoids companion-app ambiguity where JSON list values may be
    interpreted as equality-list values instead of operator expressions.
    """
    normalized = normalize_filters(doctype, filters)
    if style == "dict":
        return normalized
    output: list[list[Any]] = []
    for field, value in normalized.items():
        if isinstance(value, list) and len(value) == 2 and isinstance(value[0], str) and value[0].lower() in ALLOWED_FILTER_OPERATORS:
            output.append([doctype, field, value[0].lower(), value[1]])
        else:
            output.append([doctype, field, "=", value])
    return output


def _normalize_value(doctype: str, field: str, value: Any) -> Any:
    if field == "status" and isinstance(value, str):
        return STATUS_ALIASES.get(doctype, {}).get(value.lower(), value)
    if isinstance(value, list):
        if len(value) == 2 and isinstance(value[0], str):
            operator = _operator(value[0])
            return [operator, _validate_operator_value(operator, value[1])]
        return value
    if isinstance(value, dict):
        if "between" in value:
            return ["between", _pair(value["between"])]
        if "min" in value and "max" in value:
            return ["between", [value["min"], value["max"]]]
        if "from" in value and "to" in value:
            return ["between", [value["from"], value["to"]]]
        if "operator" in value and "value" in value:
            operator = _operator(str(value["operator"]))
            return [operator, _validate_operator_value(operator, value["value"])]
    return value


def _operator(value: str) -> str:
    operator = value.strip().lower()
    aliases = {"=>": ">=", "=<": "<=", "notin": "not in"}
    operator = aliases.get(operator, operator)
    if operator not in ALLOWED_FILTER_OPERATORS:
        raise FilterNormalizationError(f"Invalid filter operator: {value}")
    return operator


def _validate_operator_value(operator: str, value: Any) -> Any:
    if operator == "between":
        return _pair(value)
    if operator in {"in", "not in"} and not isinstance(value, list):
        return [value]
    return value


def _pair(value: Any) -> list[Any]:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        raise FilterNormalizationError("Between filters require exactly two values.")
    return [value[0], value[1]]


def _list_to_dict(filters: list[Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for item in filters:
        if isinstance(item, (list, tuple)) and len(item) >= 4:
            output[str(item[1])] = [item[2], item[3]]
        elif isinstance(item, (list, tuple)) and len(item) == 3:
            output[str(item[0])] = [item[1], item[2]]
    return output
