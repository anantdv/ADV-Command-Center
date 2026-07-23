from __future__ import annotations

import re
from typing import Any

from app.utils.doctype_resolver import resolve_doctype
from app.utils.entity_extractor import RECORD_ID_PATTERN
from app.utils.context_isolation import should_use_workflow_context


WORKFLOW_ACTION_PHRASES = {
    "approve": ["approve", "approved", "accept"],
    "reject": ["reject", "rejected", "decline"],
    "send back": ["send back", "return", "send it back", "send this back"],
    "process": ["process"],
}


def parse_workflow_intent(message: str, conversation_context: Any | None = None) -> dict[str, Any] | None:
    action_intent = parse_workflow_action_intent(message, conversation_context)
    if action_intent:
        return action_intent

    text = " ".join(message.lower().split())
    doctype = resolve_doctype(message)
    docname = _document_name(message)

    if re.search(r"\b(?:pending approval|pending approvals|my pending approval|my pending approvals|documents pending for my approval|pending .* approval|pending .* approvals|approval documents)\b", text):
        return {"intent": "workflow_list_pending", "doctype": doctype}

    if re.search(r"\b(?:approval details|approval detail|workflow details|workflow detail|actions available|available actions)\b", text):
        return {"intent": "workflow_get_detail", "doctype": doctype, "record_name": docname}

    return None


def parse_workflow_action_intent(message: str, conversation_context: Any | None = None) -> dict[str, Any] | None:
    text = " ".join(message.lower().split())
    doctype = resolve_doctype(message)
    docname = _document_name(message)
    requested_action = _requested_action(message, _available_action_labels(conversation_context))
    if not requested_action:
        return None
    if docname or doctype:
        return {"intent": "workflow_apply_action", "doctype": doctype, "record_name": docname, "action": requested_action}
    if should_use_workflow_context(message):
        context = _context_dict(conversation_context)
        if context and context.get("active_doctype") and context.get("active_document"):
            return {
                "intent": "workflow_apply_action",
                "doctype": context.get("active_doctype"),
                "record_name": context.get("active_document"),
                "action": requested_action,
                "contextual": True,
            }
        return {"intent": "workflow_apply_action", "action": requested_action, "missing_context": True, "contextual": True}
    return None


def _document_name(message: str) -> str | None:
    match = RECORD_ID_PATTERN.search(message)
    if match:
        return match.group(0).upper()
    generic = re.search(r"\b([A-Z]{2,}(?:-[A-Z0-9]+){2,})\b", message, re.IGNORECASE)
    return generic.group(1).upper() if generic else None


def _requested_action(message: str, available_actions: list[str]) -> str | None:
    text = " ".join(message.lower().split())
    if available_actions:
        for action in available_actions:
            if _normalize(action) in text:
                return action
        semantic = _semantic_action_key(text)
        if semantic:
            return _best_available_action(semantic, available_actions)
    action_match = re.search(r"\b(?:apply action\s+)?([A-Za-z][A-Za-z ]{1,60}?)(?:\s+(?:to|on|for)\b|$)", message, re.I)
    if action_match:
        candidate = action_match.group(1).strip()
        semantic = _semantic_action_key(candidate)
        if semantic:
            return semantic.title() if semantic != "send back" else "Send Back"
    semantic = _semantic_action_key(text)
    return semantic.title() if semantic and semantic != "send back" else ("Send Back" if semantic == "send back" else None)


def _semantic_action_key(text: str) -> str | None:
    normalized = _normalize(text)
    for key, phrases in WORKFLOW_ACTION_PHRASES.items():
        if any(_normalize(phrase) in normalized for phrase in phrases):
            return key
    return None


def _best_available_action(semantic: str, available_actions: list[str]) -> str | None:
    semantic_norm = _normalize(semantic)
    for action in available_actions:
        action_norm = _normalize(action)
        if semantic_norm in action_norm or action_norm in semantic_norm:
            return action
    if semantic == "approve":
        return next((action for action in available_actions if "approv" in _normalize(action) or "accept" in _normalize(action)), None)
    if semantic == "reject":
        return next((action for action in available_actions if "reject" in _normalize(action) or "declin" in _normalize(action)), None)
    if semantic == "send back":
        return next((action for action in available_actions if "sendback" in _normalize(action) or "return" in _normalize(action) or "requestchange" in _normalize(action)), None)
    if semantic == "process":
        return next((action for action in available_actions if "process" in _normalize(action)), None)
    return None


def _available_action_labels(context: Any | None) -> list[str]:
    data = _context_dict(context)
    raw = data.get("active_workflow_actions") or data.get("available_actions") or []
    labels = []
    for item in raw:
        if isinstance(item, dict):
            value = item.get("action") or item.get("label")
        else:
            value = item
        if value:
            labels.append(str(value))
    return labels


def _context_dict(context: Any | None) -> dict[str, Any]:
    if context is None:
        return {}
    if hasattr(context, "model_dump"):
        return context.model_dump(mode="json")
    if isinstance(context, dict):
        return context
    return {}


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower())
