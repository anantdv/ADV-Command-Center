from __future__ import annotations

import re
from typing import Any

from app.utils.doctype_resolver import resolve_doctype
from app.utils.entity_extractor import RECORD_ID_PATTERN


def parse_workflow_intent(message: str) -> dict[str, Any] | None:
    text = " ".join(message.lower().split())
    doctype = resolve_doctype(message)
    docname = _document_name(message)

    if re.search(r"\b(?:pending approvals|documents pending for my approval|pending .* approvals)\b", text):
        return {"intent": "workflow_list_pending", "doctype": doctype}

    if re.search(r"\b(?:approval details|approval detail|workflow details|workflow detail|actions available|available actions)\b", text):
        return {"intent": "workflow_get_detail", "doctype": doctype, "record_name": docname}

    action_match = re.search(r"\b(approve|reject)\b", text)
    if action_match and (docname or doctype):
        return {"intent": "workflow_apply_action", "doctype": doctype, "record_name": docname, "action": action_match.group(1).title()}

    return None


def _document_name(message: str) -> str | None:
    match = RECORD_ID_PATTERN.search(message)
    if match:
        return match.group(0).upper()
    generic = re.search(r"\b([A-Z]{2,}(?:-[A-Z0-9]+){2,})\b", message, re.IGNORECASE)
    return generic.group(1).upper() if generic else None
