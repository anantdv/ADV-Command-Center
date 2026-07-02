import json
import re
from typing import Any

from app.llm.prompts import ALLOWED_CREATE_DOCTYPES, ALLOWED_DOCTYPES, ALLOWED_REPORTS, ALLOWED_UPDATE_DOCTYPES, BLOCKED_OPERATIONS
from app.llm.schemas import ExtractedIntent
from app.utils.field_mapper import BLOCKED_WRITE_FIELDS

SENSITIVE_FIELD_PARTS = ("password", "token", "api_key", "api_secret", "salary", "bank", "account_no", "pan", "aadhaar")
ALLOWED_OPERATORS = {"=", "!=", ">", "<", ">=", "<=", "in", "not in", "like", "between"}
SQL_PATTERN = re.compile(r"(?:\bselect\b|\bunion\b|\bdrop\b|\binsert\b|\bdelete\s+from\b|--|;)", re.I)


def validate_extracted_intent(intent: ExtractedIntent) -> ExtractedIntent:
    values = intent.model_copy(deep=True)
    summary = " ".join(filter(None, [values.blocked_reason, values.user_facing_summary])).lower()
    if any(term in summary for term in BLOCKED_OPERATIONS):
        values.intent = "blocked_write"; values.operation = "blocked"
    if values.doctype and values.doctype not in ALLOWED_DOCTYPES:
        values.intent = "unsupported"; values.doctype = None
    if values.report_name and values.report_name not in ALLOWED_REPORTS:
        values.intent = "unsupported"; values.report_name = None
    if values.intent == "crud_create" and values.doctype not in ALLOWED_CREATE_DOCTYPES:
        values.intent = "blocked_write"; values.operation = "blocked"
    if values.intent == "crud_update" and values.doctype not in ALLOWED_UPDATE_DOCTYPES:
        values.intent = "blocked_write"; values.operation = "blocked"
    blocked = set(BLOCKED_WRITE_FIELDS)
    values.fields = [field for field in values.fields if not _sensitive(field) and field not in blocked]
    values.data = {key:value for key,value in values.data.items() if not _sensitive(key) and key not in blocked}
    values.filters = _sanitize_filters(values.filters)
    values.limit = min(max(int(values.limit or 20), 1), 500)
    values.confidence = min(max(float(values.confidence or 0), 0), 1)
    return values


def _sensitive(field: str) -> bool:
    lowered = field.lower()
    return any(part in lowered for part in SENSITIVE_FIELD_PARTS)


def _sanitize_filters(filters: dict[str, Any]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field, value in (filters or {}).items():
        if _sensitive(str(field)) or SQL_PATTERN.search(str(field)): continue
        if isinstance(value, list) and value:
            if str(value[0]).lower() not in ALLOWED_OPERATORS: continue
        try: json.dumps(value)
        except (TypeError, ValueError): continue
        if SQL_PATTERN.search(json.dumps(value)): continue
        output[str(field)] = value
    return output

