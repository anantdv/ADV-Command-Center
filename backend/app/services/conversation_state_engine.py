from __future__ import annotations

import logging
import re
from time import perf_counter
from typing import Any

from app.schemas.chat import AssistantChatResponse, ChatMessageRequest
from app.schemas.conversation_state import ConversationContext, ConversationState, StateDecision
from app.utils.datetime import utc_now
from app.utils.workflow_intent_parser import parse_workflow_intent

logger = logging.getLogger(__name__)


DOCTYPE_ABBREVIATIONS = {
    "po": "purchase order",
    "pi": "purchase invoice",
    "so": "sales order",
    "si": "sales invoice",
    "dn": "delivery note",
    "mr": "material request",
    "pr": "purchase receipt",
    "je": "journal entry",
    "pe": "payment entry",
    "rfq": "request for quotation",
}


class ConversationStateEngine:
    """State-first routing layer for Command Center conversations.

    The engine does not execute ERPNext actions. It loads the current workflow
    context, normalizes the command, and chooses the continuation route before
    LLM/router classification is allowed to run.
    """

    async def load_context(self, repository: Any, conversation_id: str) -> ConversationContext:
        context = await repository.get_conversation_context(conversation_id)
        if context:
            return context
        return ConversationContext(conversation_id=conversation_id, active_state=ConversationState.IDLE)

    def decide(self, request: ChatMessageRequest, context: ConversationContext, has_pending_draft: bool, has_report: bool) -> StateDecision:
        normalized = normalize_business_abbreviations(request.message)
        action = request.structured_action or {}
        active = context.active_state
        if action.get("action") == "select_entity_match":
            return StateDecision(route="structured_selection", normalized_message=normalized, active_state=active, reason="structured entity selection")
        if action.get("action") in {"select_draft_field_value", "set_child_row_field", "set_field_for_rows"}:
            return StateDecision(route="structured_draft_field", normalized_message=normalized, active_state=active, reason="structured draft field selection")
        if looks_like_workflow_request(normalized):
            return StateDecision(route="general_router", normalized_message=normalized, active_state=active, reason="workflow request")
        if has_pending_draft and not looks_like_new_draft(normalized):
            return StateDecision(route="draft_continue", normalized_message=normalized, active_state=active, reason="active draft session")
        if has_report and looks_like_report_followup(normalized):
            return StateDecision(route="report_followup", normalized_message=normalized, active_state=active, reason="active report context")
        if looks_like_new_draft(normalized):
            return StateDecision(route="new_draft", normalized_message=normalized, active_state=active, reason="new draft request")
        return StateDecision(route="general_router", normalized_message=normalized, active_state=active, reason="no active continuation")

    async def transition(
        self,
        repository: Any,
        context: ConversationContext,
        response: AssistantChatResponse,
        previous_state: ConversationState | None = None,
        route: str | None = None,
        error: str | None = None,
    ) -> ConversationContext:
        started = perf_counter()
        new_state = state_from_response(response)
        workflow_context = _response_workflow_context(response)
        updated = context.model_copy(update={
            "active_state": new_state,
            "active_plan_id": _response_plan_id(response) or context.active_plan_id,
            "draft_session_id": response.conversation_id if new_state.name.startswith("DRAFT") or new_state in {ConversationState.ENTITY_SELECTION, ConversationState.WAITING_USER_SELECTION, ConversationState.WAITING_USER_CONFIRMATION} else context.draft_session_id,
            "report_session_id": _response_report_id(response) or context.report_session_id,
            "active_doctype": _response_doctype(response) or context.active_doctype,
            "active_document": (workflow_context or {}).get("name") or _response_document_name(response) or context.active_document,
            "active_workflow_state": (workflow_context or {}).get("workflow_state") or context.active_workflow_state,
            "active_workflow_actions": (workflow_context or {}).get("available_actions") or context.active_workflow_actions,
            "expected_field": _response_expected_field(response),
            "expected_entity_type": _response_expected_entity_type(response),
            "pending_entities": _response_pending_entities(response),
            "confirmation_token": _response_confirmation_id(response),
            "preview_version": _response_preview_version(response) or context.preview_version,
            "last_ai_response": response.content,
            "last_action_timestamp": utc_now().isoformat(),
        })
        if new_state in {ConversationState.DRAFT_CANCELLED, ConversationState.DRAFT_COMPLETED, ConversationState.IDLE}:
            updated.draft_session_id = None
            updated.confirmation_token = None
            updated.expected_field = None
            updated.expected_entity_type = None
            updated.pending_entities = []
        if workflow_context and not workflow_context.get("available_actions"):
            updated.active_workflow_actions = []
        await repository.save_conversation_context(response.conversation_id, updated)
        response.current_state = updated.active_state.value
        response.response_type = response_type_from_state(response, updated.active_state)
        response.next_expected_action = next_expected_action(updated.active_state)
        response.available_actions = available_actions(updated.active_state)
        logger.info("conversation_state_transition", extra={
            "conversation_id": response.conversation_id,
            "previous_state": (previous_state or context.active_state).value,
            "new_state": updated.active_state.value,
            "intent": response.intent,
            "route": route,
            "draft_id": updated.draft_session_id,
            "report_id": updated.report_session_id,
            "duration_ms": int((perf_counter() - started) * 1000),
            "error": error,
        })
        return updated


def normalize_business_abbreviations(message: str) -> str:
    output = f" {message} "
    for abbreviation, full in DOCTYPE_ABBREVIATIONS.items():
        output = re.sub(rf"(?i)(?<![\w-]){re.escape(abbreviation)}(?![\w-])", full, output)
    return " ".join(output.split())


def looks_like_new_draft(message: str) -> bool:
    text = message.lower()
    return bool(re.search(r"\b(create|add|draft|prepare|make|raise|enter)\b", text) and re.search(r"\b(purchase order|purchase invoice|sales order|sales invoice|quotation|delivery note|material request|stock entry|customer|supplier|item|issue|task|project)\b", text))


def looks_like_report_followup(message: str) -> bool:
    text = message.lower()
    return any(phrase in text for phrase in ("this result", "same filters", "show detail", "row ", "sort by", "export", "summarize", "chart", "group by", "drill down", "pin"))


def looks_like_workflow_request(message: str) -> bool:
    return parse_workflow_intent(message) is not None


def state_from_response(response: AssistantChatResponse) -> ConversationState:
    if response.intent == "child_rows_resolution_required":
        return ConversationState.DRAFT_ENTITY_RESOLUTION
    if response.intent == "draft_field_options":
        return ConversationState.DRAFT_INFORMATION_REQUIRED
    if response.intent == "draft_preview_updated":
        return ConversationState.DRAFT_PREVIEW
    if response.intent == "show_draft_fields":
        return ConversationState.DRAFT_PREVIEW
    if response.intent == "draft_cancelled":
        return ConversationState.DRAFT_CANCELLED
    if response.intent in {"crud_create", "crud_update"}:
        if any(getattr(part, "type", "") == "record_preview" for part in response.parts):
            return ConversationState.DRAFT_PREVIEW
        if any(getattr(part, "type", "") == "missing_fields" for part in response.parts):
            return ConversationState.DRAFT_INFORMATION_REQUIRED
        return ConversationState.DRAFT_COLLECTING
    if response.intent in {"visualize_existing_report", "regroup_existing_report", "export_existing_report", "pin_existing_report", "run_report", "run_analytics", "generate_chart", "chart_result", "list_records", "chart_query", "summary_query"}:
        return ConversationState.REPORT_READY
    if response.intent == "get_record":
        return ConversationState.REPORT_DETAIL
    if response.intent == "workflow_list_pending":
        return ConversationState.WORKFLOW_READY
    if response.intent in {"workflow_get_detail", "workflow_apply_action"}:
        return ConversationState.WORKFLOW_DETAIL
    if response.intent.endswith("failed"):
        return ConversationState.ERROR
    return ConversationState.IDLE


def response_type_from_state(response: AssistantChatResponse, state: ConversationState) -> str:
    if response.intent == "show_draft_fields":
        return "draft_inspection"
    if state == ConversationState.DRAFT_PREVIEW:
        return "draft_preview"
    if state in {ConversationState.DRAFT_ENTITY_RESOLUTION, ConversationState.ENTITY_SELECTION}:
        return "entity_selection"
    if state == ConversationState.DRAFT_INFORMATION_REQUIRED:
        return "draft_information_required"
    if state == ConversationState.REPORT_READY:
        return "report_result"
    if state == ConversationState.REPORT_DETAIL:
        return "document_detail"
    if state == ConversationState.WORKFLOW_READY:
        return "workflow_list_pending"
    if state == ConversationState.WORKFLOW_DETAIL:
        return "workflow_detail"
    if state == ConversationState.ERROR:
        return "error"
    return response.intent


def next_expected_action(state: ConversationState) -> str | None:
    return {
        ConversationState.DRAFT_ENTITY_RESOLUTION: "selection",
        ConversationState.DRAFT_INFORMATION_REQUIRED: "user_input",
        ConversationState.DRAFT_PREVIEW: "confirmation",
        ConversationState.REPORT_READY: "follow_up",
        ConversationState.WORKFLOW_READY: "workflow_selection",
        ConversationState.WORKFLOW_DETAIL: "workflow_action",
        ConversationState.WAITING_USER_CONFIRMATION: "confirmation",
    }.get(state)


def available_actions(state: ConversationState) -> list[str]:
    return {
        ConversationState.DRAFT_ENTITY_RESOLUTION: ["select", "search_again", "cancel"],
        ConversationState.DRAFT_INFORMATION_REQUIRED: ["provide_value", "cancel"],
        ConversationState.DRAFT_PREVIEW: ["inspect", "edit", "confirm", "cancel"],
        ConversationState.REPORT_READY: ["chart", "export", "detail", "pin", "refine"],
        ConversationState.WORKFLOW_READY: ["open", "refresh"],
        ConversationState.WORKFLOW_DETAIL: ["approve", "reject", "send_back", "refresh"],
    }.get(state, [])


def _response_confirmation_id(response: AssistantChatResponse) -> str | None:
    for part in response.parts:
        if getattr(part, "type", "") == "confirmation":
            return getattr(part, "confirmation_id", None)
    return None


def _response_plan_id(response: AssistantChatResponse) -> str | None:
    for part in response.parts:
        if getattr(part, "type", "") == "execution_plan":
            return getattr(part, "plan_id", None)
    return None


def _response_preview_version(response: AssistantChatResponse) -> int | None:
    for part in response.parts:
        if getattr(part, "type", "") == "record_preview":
            return getattr(part, "draft_version", None)
        if getattr(part, "type", "") == "draft_inspection":
            return getattr(part, "draft_version", None)
    return None


def _response_report_id(response: AssistantChatResponse) -> str | None:
    for part in response.parts:
        config = getattr(part, "config", None)
        if isinstance(config, dict) and config.get("report_id"):
            return str(config["report_id"])
    return None


def _response_doctype(response: AssistantChatResponse) -> str | None:
    if response.source and response.source.doctype:
        return response.source.doctype
    for part in response.parts:
        if getattr(part, "doctype", None):
            return getattr(part, "doctype")
    return None


def _response_document_name(response: AssistantChatResponse) -> str | None:
    if response.source and response.source.filters:
        value = response.source.filters.get("name") or response.source.filters.get("record_name")
        if value:
            return str(value)
    for part in response.parts:
        if getattr(part, "name", None):
            return getattr(part, "name")
    return None


def _response_workflow_context(response: AssistantChatResponse) -> dict[str, Any] | None:
    for part in response.parts:
        if getattr(part, "type", "") != "record_detail":
            continue
        actions = list(getattr(part, "available_workflow_actions", []) or [])
        if not actions:
            return None
        return {
            "doctype": getattr(part, "doctype", None),
            "name": getattr(part, "name", None),
            "workflow_state": getattr(part, "workflow_state", None),
            "available_actions": actions,
        }
    if response.intent == "workflow_apply_action" and response.source and response.source.filters:
        filters = response.source.filters
        return {
            "doctype": filters.get("doctype"),
            "name": filters.get("name"),
            "workflow_state": filters.get("new_state") or filters.get("workflow_state"),
            "available_actions": filters.get("available_actions") or [],
        }
    return None


def _response_expected_field(response: AssistantChatResponse) -> str | None:
    for part in response.parts:
        if getattr(part, "type", "") == "draft_field_options":
            return getattr(part, "fieldname", None)
        if getattr(part, "type", "") == "child_rows_resolution_required":
            rows = list(getattr(part, "rows", []) or [])
            if len(rows) == 1:
                return getattr(rows[0], "link_field", None)
    return None


def _response_expected_entity_type(response: AssistantChatResponse) -> str | None:
    fieldname = _response_expected_field(response)
    return {
        "supplier": "Supplier",
        "customer": "Customer",
        "party_name": "Customer",
        "item_code": "Item",
        "warehouse": "Warehouse",
        "company": "Company",
        "currency": "Currency",
    }.get(str(fieldname or ""))


def _response_pending_entities(response: AssistantChatResponse) -> list[dict[str, Any]]:
    for part in response.parts:
        if getattr(part, "type", "") != "child_rows_resolution_required":
            continue
        table_field = getattr(part, "table_field", None)
        output = []
        for row in getattr(part, "rows", []) or []:
            output.append({
                "table_field": table_field,
                "row_id": getattr(row, "row_id", None),
                "fieldname": getattr(row, "link_field", None),
                "query": getattr(row, "query", None),
                "status": getattr(row, "status", None),
            })
        return output
    return []


conversation_state_engine = ConversationStateEngine()
