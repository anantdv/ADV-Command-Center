import logging
import re
from time import perf_counter
from typing import Any

from app.agents.erp_data_agent import ERPDataAgent
from app.agents.aggregation_agent import AggregationAgent
from app.agents.analytics_agent import AnalyticsAgent
from app.agents.workflow_agent import WorkflowAgent
from app.agents.file_generation_agent import FileGenerationAgent
from app.agents.crud_agent import CrudAgent
from app.agents.report_agent import ReportAgent
from app.agents.report_composer_agent import ReportComposerAgent
from app.agents.router_agent import IntentResult, RouterAgent
from app.agents.safety_agent import SafetyAgent, SafetyResult
from app.core.audit import AuditEvent, log_audit_event
from app.config import settings
from app.schemas.chat import (
    AssistantChatResponse,
    ChatActionResult,
    ChatMessage,
    ChatMessageRequest,
    Conversation,
    ConversationCreate,
    ExtractionMeta,
    PermissionMeta,
    SourceMeta,
    SuggestedAction,
    TablePart,
    MissingFieldsPart,
    RecordPreviewPart,
    DraftFieldOption,
    DraftFieldOptionsPart,
    TextPart,
    ToolCallPart,
    ChartPart,
    ChildRowsResolutionPart,
    ConfirmationPart,
)
from app.schemas.aggregation import AggregationMetric, AggregationPlan
from app.schemas.crud import CancelCrudResponse, ConfirmCrudRequest, ConfirmCrudResponse, ContinueCrudRequest
from app.schemas.dashboard import DashboardWidgetSource, PinChatResultRequest, PinChatResultResponse
from app.services.dashboard_service import DashboardService, dashboard_service
from app.services.conversation_repository import InMemoryConversationRepository
from app.services.suggestion_service import SuggestionService, suggestion_service
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.suggestion_context_builder import SuggestionContextBuilder
from app.utils.table_formatter import build_table_part
from app.utils.chart_data_normalizer import normalize_chart_data
from app.utils.payload_builder import PayloadBuilder
from app.utils.confirmation_store import confirmation_store
from app.schemas.entity_resolution import ChildRowResolution, EntitySearchContext, EntitySearchRequest
from app.services.entity_resolution_service import entity_resolution_service

logger = logging.getLogger(__name__)

CLARIFICATION_MESSAGE = "I could not determine the requested report operation."


class ChatService:
    """Orchestrates classification, safety, read-only tools, persistence, and audit."""

    def __init__(
        self,
        router: RouterAgent | None = None,
        safety: SafetyAgent | None = None,
        erp_agent: ERPDataAgent | None = None,
        report_agent: ReportAgent | None = None,
        repository: InMemoryConversationRepository | None = None,
        file_agent: FileGenerationAgent | None = None,
        dashboards: DashboardService | None = None,
        crud_agent: CrudAgent | None = None,
        aggregation_agent: AggregationAgent | None = None,
        analytics_agent: AnalyticsAgent | None = None,
        workflow_agent: WorkflowAgent | None = None,
        report_composer_agent: ReportComposerAgent | None = None,
        suggestions: SuggestionService | None = None,
    ) -> None:
        self.router = router or RouterAgent()
        self.safety = safety or SafetyAgent()
        self.erp_agent = erp_agent or ERPDataAgent()
        self.report_agent = report_agent or ReportAgent()
        self.repository = repository or InMemoryConversationRepository()
        self.file_agent = file_agent or FileGenerationAgent()
        self.dashboards = dashboards or dashboard_service
        self.crud_agent = crud_agent or CrudAgent()
        self.aggregation_agent = aggregation_agent or AggregationAgent()
        self.analytics_agent = analytics_agent or AnalyticsAgent()
        self.workflow_agent = workflow_agent or WorkflowAgent()
        self.report_composer_agent = report_composer_agent or ReportComposerAgent()
        self.suggestions = suggestions or suggestion_service
        self.suggestion_context = SuggestionContextBuilder()

    async def list_conversations(self) -> list[Conversation]:
        return await self.repository.list_conversations()

    async def create_conversation(self, request: ConversationCreate) -> Conversation:
        return await self.repository.create_conversation(request.title or "New command")

    async def get_messages(self, conversation_id: str) -> list[ChatMessage]:
        return await self.repository.get_messages(conversation_id)

    async def send_chat_message(
        self,
        request: ChatMessageRequest,
        cookies: dict | None = None,
        user: str = "unknown",
        user_roles: list[str] | None = None,
    ) -> AssistantChatResponse:
        started = perf_counter()
        route = "unresolved"
        safety = SafetyResult(allowed=True, reason=None, risk_level="low")
        conversation = await self.repository.get_or_create(
            request.conversation_id,
            self._conversation_title(request.message),
        )
        await self.repository.save_message(
            ChatMessage(
                id=new_id("msg"),
                conversation_id=conversation.id,
                role="user",
                content=request.message,
                created_at=utc_now(),
            )
        )

        selection_response = await self._handle_entity_selection_action(request, conversation.id, cookies, user)
        if selection_response:
            intent = IntentResult(intent="crud_create", conversation_id=conversation.id, raw_prompt=request.message, confidence=1)
            response = selection_response
            route = "entity_selection"
            response.extraction = ExtractionMeta(method="rules", confidence=1, erp_data_sent=False)
            await self._remember_pending_draft(response)
            await self._persist_response(response)
            await self._audit(user, request.message, intent, response, safety)
            logger.info("chat_command_executed", extra={"conversation_id": conversation.id, "command_id": response.message_id, "source": "generated_action", "resolved_intent": response.intent, "execution_route": route, "response_type": response.intent, "duration_ms": int((perf_counter() - started) * 1000), "error": None})
            return response

        draft_field_response = await self._handle_draft_field_action(request, conversation.id, cookies, user)
        if draft_field_response:
            intent = IntentResult(intent="crud_create", conversation_id=conversation.id, raw_prompt=request.message, confidence=1)
            response = draft_field_response
            route = "draft_field_selection"
            response.extraction = ExtractionMeta(method="rules", confidence=1, erp_data_sent=False)
            await self._remember_pending_draft(response)
            await self._persist_response(response)
            await self._audit(user, request.message, intent, response, safety)
            logger.info("chat_command_executed", extra={"conversation_id": conversation.id, "command_id": response.message_id, "source": "generated_action", "resolved_intent": response.intent, "execution_route": route, "response_type": response.intent, "duration_ms": int((perf_counter() - started) * 1000), "error": None})
            return response

        fresh_draft_intent = self.router._planned_create_intent(request.message)
        if fresh_draft_intent and await self.repository.get_pending_draft(conversation.id):
            await self.repository.supersede_pending_draft(conversation.id, new_id("draft"))
            await self.repository.clear_pending_draft(conversation.id)
            fresh_draft_intent.conversation_id = conversation.id
            response = await self._prepare_crud_or_resolve_entities(fresh_draft_intent, conversation.id, cookies, user)
            intent = fresh_draft_intent
            route = "document_planner_new_session"
            response.extraction = ExtractionMeta(method="rules", confidence=1, erp_data_sent=False)
            await self._remember_pending_draft(response)
            await self._persist_response(response)
            await self._audit(user, request.message, intent, response, safety)
            logger.info("chat_command_executed", extra={"conversation_id": conversation.id, "command_id": response.message_id, "source": request.source or "typed", "resolved_intent": intent.intent, "execution_route": route, "new_session_created": True, "prior_session_superseded": True, "response_type": response.intent, "duration_ms": int((perf_counter() - started) * 1000), "error": None})
            return response

        pending_response = await self._maybe_continue_pending_draft(request, conversation.id, cookies, user)
        if pending_response:
            audit_intent = "crud_create" if pending_response.intent in {"child_rows_resolution_required", "draft_cancelled", "draft_field_options", "draft_preview_updated", "draft_edit_failed"} else pending_response.intent
            intent = IntentResult(
                intent=audit_intent,
                conversation_id=conversation.id,
                raw_prompt=request.message,
                confidence=1,
            )
            response = pending_response
            route = "document_planner_continue"
            response.extraction = ExtractionMeta(method="rules", confidence=1, erp_data_sent=False)
            await self._remember_pending_draft(response)
            await self._persist_response(response)
            await self._audit(user, request.message, intent, response, safety)
            logger.info("chat_command_executed", extra={"conversation_id": conversation.id, "command_id": response.message_id, "source": request.source or "typed", "resolved_intent": intent.intent, "execution_route": route, "response_type": response.intent, "duration_ms": int((perf_counter() - started) * 1000), "error": None})
            return response

        followup = await self._resolve_report_followup(request, conversation.id)
        if followup:
            route = "report_followup"
            intent = IntentResult(
                intent=followup["intent"],
                conversation_id=conversation.id,
                raw_prompt=request.message,
                confidence=1,
                filters=followup.get("context", {}).get("filters") or {},
                doctype=followup.get("context", {}).get("doctype"),
                report_name=followup.get("context", {}).get("report_name"),
            )
            response = await self._handle_report_followup(followup, conversation.id, cookies, user)
        else:
            intent = await self.router.classify(request.message, request.module_context, user, conversation.id, request.date_range)
            intent.conversation_id = conversation.id
            if intent.intent == "generate_file" and intent.source_type == "chat_result":
                self._attach_previous_result(intent, await self.repository.get_messages(conversation.id))
            safety = await self.safety.validate(intent)

            if not safety.allowed:
                route = "safety_block"
                response = self._blocked_response(conversation.id, intent, safety)
            elif intent.intent in {"workflow_list_pending", "workflow_get_detail", "workflow_apply_action"}:
                route = "workflow"
                response = await self.workflow_agent.handle(intent, cookies, user)
            elif intent.intent == "run_report":
                route = "report"
                response = await self.report_agent.handle(intent, cookies)
            elif intent.intent in {"run_analytics", "generate_chart"}:
                route = "analytics"
                response = await self.analytics_agent.handle(intent, cookies, user)
            elif intent.intent == "generate_file":
                route = "file_generation"
                response = await self.file_agent.handle(intent, cookies, user)
            elif intent.intent in {"crud_create", "crud_update"}:
                route = "crud_preview"
                response = await self._prepare_crud_or_resolve_entities(intent, conversation.id, cookies, user)
            elif intent.intent == "report_composer":
                route = "report_composer"
                response = await self.report_composer_agent.handle(intent, cookies, user)
            elif intent.intent == "pin_to_dashboard":
                route = "pin"
                response = await self._pin_intent(intent, cookies, user)
            elif intent.aggregation and intent.aggregation.enabled and intent.query_plan:
                route = "aggregation"
                response = await self.aggregation_agent.handle(intent.query_plan, cookies, user, conversation.id)
            elif intent.intent in {"list_records", "get_record", "summary_query", "chart_query", "write_blocked"}:
                route = "erp_data"
                response = await self.erp_agent.handle(intent, cookies)
            else:
                route = "clarification"
                response = self._unsupported_response(conversation.id, intent.missing_info_hint)

        response.extraction = ExtractionMeta(
            method=intent.extraction_method,
            confidence=intent.llm_confidence or intent.confidence,
            provider=intent.llm_provider,
            model=intent.llm_model,
            privacy_checked=intent.privacy_checked,
            privacy_allowed=intent.privacy_allowed,
            erp_data_sent=False,
            fallback_used=intent.fallback_used,
        )
        await self._remember_report_context(response, intent, request)
        await self._remember_pending_draft(response)
        await self._attach_suggestions(response, request.message, intent, cookies, user, user_roles or [])
        await self._persist_response(response)
        await self._audit(user, request.message, intent, response, safety)
        logger.info(
            "chat_command_executed",
            extra={
                "conversation_id": conversation.id,
                "command_id": response.message_id,
                "source": request.source or (request.structured_action or {}).get("source") or "typed",
                "structured_action": self._safe_action_summary(request.structured_action),
                "resolved_intent": intent.intent,
                "active_report_id": request.active_report_id or (request.structured_action or {}).get("report_id"),
                "active_result_id": request.active_result_id or (request.structured_action or {}).get("result_id"),
                "filters_loaded": bool(response.source and response.source.filters),
                "execution_route": route,
                "erpnext_query_executed": route not in {"report_followup", "clarification"} or (followup or {}).get("requeried", False),
                "response_type": response.intent,
                "duration_ms": int((perf_counter() - started) * 1000),
                "error": None,
            },
        )
        return response

    async def continue_crud(self, request: ContinueCrudRequest, cookies: dict | None = None, user: str = "unknown") -> AssistantChatResponse:
        data = dict(request.data or {})
        if request.operation == "create" and isinstance(data.get("items"), str):
            data["items"] = PayloadBuilder._extract_natural_items(str(data["items"]))
        intent = IntentResult(
            intent="crud_create" if request.operation == "create" else "crud_update",
            operation=request.operation,
            doctype=request.doctype,
            record_name=request.record_name,
            data=data,
            conversation_id=request.conversation_id,
            raw_prompt=f"continue {request.operation} {request.doctype}",
            confidence=1,
        )
        response = await self._prepare_crud_or_resolve_entities(intent, request.conversation_id or new_id("conv"), cookies, user)
        await self._remember_pending_draft(response)
        await self._persist_response(response)
        return response

    async def _prepare_crud_or_resolve_entities(self, intent: IntentResult, conversation_id: str, cookies: dict | None, user: str) -> AssistantChatResponse:
        draft_changes: list[dict[str, Any]] = []
        if intent.intent == "crud_create" and intent.doctype:
            intent.data = await self._hydrate_draft_data(intent.doctype, intent.data or {}, cookies)
            draft_changes = list((intent.data or {}).pop("_last_changes", []) or [])
            resolution = await self._build_child_row_resolution(intent.doctype, intent.data or {}, conversation_id, cookies)
            if resolution:
                message_id = new_id("msg")
                summary = "I found item rows in your request. Please choose the matching ERPNext records before I prepare the draft preview."
                await self.repository.save_pending_draft(conversation_id, {"doctype": intent.doctype, "operation": "create", "data": intent.data or {}, "message_id": message_id, "status": "resolving_entities"})
                return AssistantChatResponse(conversation_id=conversation_id, message_id=message_id, intent="child_rows_resolution_required", parts=[TextPart(content=summary), resolution], permission=PermissionMeta(allowed=True, risk_level="medium", confirmation_required=True), id=message_id, content=summary, created_at=utc_now())
            readiness = self._evaluate_draft_readiness(intent.doctype, intent.data or {})
            if not readiness["ready"]:
                warehouse_blocked = any(item.get("fieldname") == "warehouse" for item in readiness["blocking_requirements"])
                if warehouse_blocked:
                    response = await self._draft_warehouse_options_response(conversation_id, intent.doctype, intent.data or {}, cookies, intent.raw_prompt)
                    await self.repository.save_pending_draft(conversation_id, {"doctype": intent.doctype, "operation": "create", "data": intent.data or {}, "message_id": response.message_id, "status": "awaiting_warehouse", "blocking_requirements": readiness["blocking_requirements"]})
                    return response
        response = await self.crud_agent.handle(intent, cookies, user)
        if draft_changes:
            preview = next((part for part in response.parts if isinstance(part, RecordPreviewPart)), None)
            if preview:
                preview.changes = draft_changes
                response.intent = "draft_preview_updated"
                response.content = "I updated the draft preview. Please review the refreshed values before confirming."
                first_text = next((part for part in response.parts if isinstance(part, TextPart)), None)
                if first_text:
                    first_text.content = response.content
        return response

    async def confirm_crud(self, request: ConfirmCrudRequest, cookies: dict | None = None, user: str = "unknown") -> ConfirmCrudResponse:
        return await self.crud_agent.tools.confirm_crud_action(request.confirmation_id, cookies, user)

    async def cancel_crud(self, request: ConfirmCrudRequest, user: str = "unknown") -> CancelCrudResponse:
        cancelled = await self.crud_agent.tools.cancel_crud_action(request.confirmation_id, user)
        return CancelCrudResponse(cancelled=cancelled)

    async def send_message(
        self,
        request: ChatMessageRequest,
        cookies: dict | None = None,
        user: str = "unknown",
        user_roles: list[str] | None = None,
    ) -> AssistantChatResponse:
        """Backward-compatible method name for existing service callers."""
        return await self.send_chat_message(request, cookies, user, user_roles)

    async def action(self, action_id: str, confirmed: bool) -> ChatActionResult:
        return ChatActionResult(action_id=action_id, status="confirmed" if confirmed else "cancelled")

    async def pin_to_dashboard(self, request: PinChatResultRequest, cookies: dict | None = None, user: str = "unknown") -> PinChatResultResponse:
        widget = await self.dashboards.pin_from_chat(request, cookies, user)
        return PinChatResultResponse(widget_id=widget.widget_id, title=widget.title)

    async def _pin_intent(self, intent: IntentResult, cookies: dict | None, user: str) -> AssistantChatResponse:
        if not intent.doctype and not intent.report_name:
            return self._unsupported_response(intent.conversation_id or new_id("conv"), intent.missing_info_hint)
        message_id=new_id("msg")
        source_type="report" if intent.report_name else "doctype"
        source_name=intent.report_name or intent.doctype or "ERPNext"
        source=DashboardWidgetSource(source_type=source_type,source_name=source_name,doctype=intent.doctype,report_name=intent.report_name,filters=intent.filters or {},fields=intent.fields)
        widget_type=intent.widget_type or "table"
        request=PinChatResultRequest(conversation_id=intent.conversation_id or new_id("conv"),message_id=message_id,title=f"{source_name} — Tinni",widget_type=widget_type,source=source)
        widget=await self.dashboards.pin_from_chat(request,cookies,user)
        summary=f"I pinned {widget.title} to Overview. Its data will refresh through your current ERPNext permissions."
        return AssistantChatResponse(conversation_id=request.conversation_id,message_id=message_id,intent="pin_to_dashboard",parts=[TextPart(content=summary),ToolCallPart(tool_name="pin_to_dashboard",status="success",input_summary=source_name,output_summary=f"Widget {widget.widget_id} created")],source=SourceMeta(source_type=source_type,source_name=source_name,filters=intent.filters or {},doctype=intent.doctype,report_name=intent.report_name,fields=intent.fields),permission=PermissionMeta(allowed=True,risk_level="medium"),suggested_actions=[SuggestedAction(label="Open Overview",action_type="open_overview")],id=message_id,content=summary,created_at=utc_now())

    async def _maybe_continue_pending_draft(self, request: ChatMessageRequest, conversation_id: str, cookies: dict | None, user: str) -> AssistantChatResponse | None:
        pending = await self.repository.get_pending_draft(conversation_id)
        if not pending:
            return None
        text = request.message.lower()
        if re.search(r"\b(cancel|start again|start over)\b", text):
            await self.repository.clear_pending_draft(conversation_id)
            message_id = new_id("msg")
            summary = "I cancelled the current draft session. You can start a new document whenever you are ready."
            return AssistantChatResponse(conversation_id=conversation_id, message_id=message_id, intent="draft_cancelled", parts=[TextPart(content=summary)], permission=PermissionMeta(allowed=True, risk_level="low"), id=message_id, content=summary, created_at=utc_now())
        doctype = str(pending.get("doctype") or "")
        if not doctype:
            return None
        collected = dict(pending.get("data") or {})
        warehouse_requirement = self._warehouse_requirement(collected) if doctype == "Purchase Order" else []
        if warehouse_requirement and self._warehouse_options_requested(text):
            return await self._draft_warehouse_options_response(conversation_id, doctype, collected, cookies, request.message)
        if warehouse_requirement:
            applied = await self._try_apply_warehouse_from_text(collected, request.message, cookies)
            if applied:
                intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=collected, conversation_id=conversation_id, raw_prompt=request.message, confidence=.98)
                return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)
        draft_updates = self._apply_natural_draft_updates(collected, request.message)
        if draft_updates["applied"]:
            self._invalidate_pending_confirmation(pending)
            collected.setdefault("_last_changes", draft_updates["changes"])
            intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=collected, conversation_id=conversation_id, raw_prompt=request.message, confidence=.99)
            return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)
        if draft_updates["matched"] and draft_updates["errors"]:
            return self._draft_edit_error_response(conversation_id, doctype, draft_updates["errors"])
        if any(word in text for word in ("show ", "list ", "open ")):
            return None
        if self._is_proceed_command(text):
            intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=collected, conversation_id=conversation_id, raw_prompt=request.message, confidence=.99)
            return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)
        removed = self._remove_matching_row(collected, request.message)
        if removed:
            intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=collected, conversation_id=conversation_id, raw_prompt=request.message, confidence=.98)
            return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)
        correction = self._apply_short_correction(collected, request.message)
        if correction:
            intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=collected, conversation_id=conversation_id, raw_prompt=request.message, confidence=.98)
            return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)
        extracted = PayloadBuilder.extract_create(doctype, request.message)
        merged = self._merge_draft_data(collected, extracted)
        intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=merged, conversation_id=conversation_id, raw_prompt=request.message, confidence=.98)
        return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)

    async def _handle_entity_selection_action(self, request: ChatMessageRequest, conversation_id: str, cookies: dict | None, user: str) -> AssistantChatResponse | None:
        action = request.structured_action or {}
        if action.get("action") != "select_entity_match":
            return None
        draft_id = str(action.get("draft_session_id") or conversation_id)
        pending = await self.repository.get_pending_draft(draft_id) or await self.repository.get_pending_draft(conversation_id)
        if not pending:
            return self._unsupported_response(conversation_id, "I could not find the draft session for that selection. Please start the draft again.")
        doctype = str(pending.get("doctype") or "")
        data = dict(pending.get("data") or {})
        table_field = str(action.get("table_field") or "items")
        fieldname = str(action.get("fieldname") or "item_code")
        row_id = str(action.get("row_id") or "")
        selected = str(action.get("selected_value") or "")
        if table_field == "__parent__":
            data[fieldname] = selected
            data.pop(f"{fieldname}_query", None)
        else:
            rows = list(data.get(table_field) or [])
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                if str(row.get("row_id") or f"row-{index+1}") == row_id:
                    row[fieldname] = selected
                    row.pop(f"{fieldname}_query", None)
                    row.pop("item_query", None)
                    if fieldname == "item_code":
                        details = await self._selected_item_defaults(selected, cookies)
                        for key, value in details.items():
                            row.setdefault(key, value)
                    rows[index] = row
                    break
            data[table_field] = rows
        intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=data, conversation_id=conversation_id, raw_prompt=request.message, confidence=1)
        return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)

    async def _handle_draft_field_action(self, request: ChatMessageRequest, conversation_id: str, cookies: dict | None, user: str) -> AssistantChatResponse | None:
        action = request.structured_action or {}
        if action.get("action") not in {"select_draft_field_value", "set_child_row_field", "set_field_for_rows"}:
            return None
        draft_id = str(action.get("draft_session_id") or conversation_id)
        pending = await self.repository.get_pending_draft(draft_id) or await self.repository.get_pending_draft(conversation_id)
        if not pending:
            return self._unsupported_response(conversation_id, "I could not find the active draft session. Please start the draft again.")
        doctype = str(pending.get("doctype") or "")
        data = dict(pending.get("data") or {})
        fieldname = str(action.get("fieldname") or "")
        value = str(action.get("selected_value") or action.get("value") or "")
        table_field = str(action.get("table_field") or "items")
        row_ids = [str(row_id) for row_id in (action.get("row_ids") or []) if row_id]
        row_id = str(action.get("row_id") or "")
        if row_id and not row_ids:
            row_ids = [row_id]
        if not fieldname or not value:
            return self._unsupported_response(conversation_id, "I could not apply that draft field selection.")
        if table_field and table_field != "__parent__":
            rows = list(data.get(table_field) or [])
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                current_id = str(row.get("row_id") or f"row-{index+1}")
                if not row_ids or current_id in row_ids:
                    row[fieldname] = value
                    rows[index] = row
            data[table_field] = rows
            if fieldname == "warehouse":
                data.setdefault("set_warehouse", value)
        else:
            data[fieldname] = value
        intent = IntentResult(intent="crud_create", operation="create", doctype=doctype, data=data, conversation_id=conversation_id, raw_prompt=request.message, confidence=1)
        return await self._prepare_crud_or_resolve_entities(intent, conversation_id, cookies, user)

    async def _build_child_row_resolution(self, doctype: str, data: dict[str, Any], conversation_id: str, cookies: dict | None) -> ChildRowsResolutionPart | None:
        output: list[ChildRowResolution] = []
        for fieldname, target_doctype in self._parent_link_fields(doctype).items():
            value = str(data.get(fieldname) or "").strip()
            if not value:
                continue
            search = await entity_resolution_service.search(EntitySearchRequest(doctype=target_doctype, query=value, context=EntitySearchContext(parent_doctype=doctype, company=str(data.get("company") or ""))), cookies)
            status, selected = entity_resolution_service.classify(search.matches)
            if status == "resolved" and selected:
                data[fieldname] = selected
                continue
            output.append(ChildRowResolution(row_id=f"parent-{fieldname}", source_text=value, status=status, extracted={}, link_field=fieldname, query=value, matches=search.matches, message=f"Please select the ERPNext {target_doctype}."))
        rows = data.get("items")
        if not isinstance(rows, list) or not rows:
            if output:
                return ChildRowsResolutionPart(draft_session_id=conversation_id, doctype=doctype, table_field="__parent__", rows=output)
            return None
        for index, row in enumerate(rows):
            if not isinstance(row, dict) or row.get("item_code"):
                continue
            query = str(row.get("item_query") or row.get("item_name") or row.get("description") or "").strip()
            if not query:
                continue
            row.setdefault("row_id", f"row-{index+1}")
            search = await entity_resolution_service.search(EntitySearchRequest(doctype="Item", query=query, context=EntitySearchContext(parent_doctype=doctype, company=str(data.get("company") or ""), supplier=str(data.get("supplier") or ""), warehouse=str(row.get("warehouse") or ""))), cookies)
            status, selected = entity_resolution_service.classify(search.matches)
            if status == "resolved" and selected:
                row["item_code"] = selected
                row.pop("item_query", None)
                details = await self._selected_item_defaults(selected, cookies)
                for key, value in details.items():
                    row.setdefault(key, value)
                continue
            output.append(ChildRowResolution(row_id=str(row["row_id"]), source_text=str(row.get("source_text") or query), status=status, extracted={key: value for key, value in row.items() if key in {"qty", "rate", "uom", "warehouse", "schedule_date", "delivery_date", "description"} and value not in (None, "")}, link_field="item_code", query=query, matches=search.matches, message="Please select the ERPNext Item." if status == "needs_selection" else "No permitted Item matched this text."))
        if output:
            data["items"] = rows
            table_field = "items" if any(row.row_id.startswith("row-") for row in output) else "__parent__"
            return ChildRowsResolutionPart(draft_session_id=conversation_id, doctype=doctype, table_field=table_field, rows=output)
        return None

    @staticmethod
    def _parent_link_fields(doctype: str) -> dict[str, str]:
        mapping = {
            "Purchase Order": {"supplier": "Supplier"},
            "Purchase Invoice": {"supplier": "Supplier"},
            "Purchase Receipt": {"supplier": "Supplier"},
            "Sales Order": {"customer": "Customer"},
            "Sales Invoice": {"customer": "Customer"},
            "Quotation": {"party_name": "Customer"},
            "Delivery Note": {"customer": "Customer"},
            "Material Request": {},
            "Stock Entry": {"from_warehouse": "Warehouse", "to_warehouse": "Warehouse"},
        }
        return mapping.get(doctype, {})

    async def _selected_item_defaults(self, item_code: str, cookies: dict | None) -> dict[str, Any]:
        try:
            record = (await entity_resolution_service.erp.get_record("Item", item_code, ["name", "item_name", "description", "stock_uom", "is_stock_item", "default_warehouse"], cookies)).record
            defaults = {"item_name": record.get("item_name"), "description": record.get("description") or record.get("item_name"), "uom": record.get("stock_uom"), "is_stock_item": record.get("is_stock_item", 1)}
            if record.get("default_warehouse"):
                defaults["warehouse"] = record.get("default_warehouse")
            return defaults
        except Exception:
            return {}

    @staticmethod
    def _merge_draft_data(base: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
        merged = dict(base or {})
        for key, value in (incoming or {}).items():
            if key == "items" and isinstance(value, list):
                merged["items"] = [*(merged.get("items") or []), *value]
            elif value not in (None, "", []):
                merged[key] = value
        return merged

    async def _hydrate_draft_data(self, doctype: str, data: dict[str, Any], cookies: dict | None) -> dict[str, Any]:
        hydrated = dict(data or {})
        rows = hydrated.get("items")
        if not isinstance(rows, list):
            hydrated.pop("_last_changes", None)
            return hydrated
        default_warehouse = hydrated.get("set_warehouse") or hydrated.get("warehouse")
        new_rows: list[dict[str, Any]] = []
        for index, item in enumerate(rows):
            if not isinstance(item, dict):
                continue
            row = dict(item)
            row.setdefault("row_id", f"row-{index+1}")
            if row.get("item_code") and (not row.get("uom") or not row.get("description") or not row.get("item_name")):
                details = await self._selected_item_defaults(str(row["item_code"]), cookies)
                for key, value in details.items():
                    row.setdefault(key, value)
            if default_warehouse and doctype in {"Purchase Order", "Purchase Invoice", "Purchase Receipt", "Sales Order", "Sales Invoice", "Delivery Note", "Material Request"}:
                row.setdefault("warehouse", default_warehouse)
            qty = self._to_float(row.get("qty"), 1)
            rate = self._to_float(row.get("rate"), 0)
            row["qty"] = qty
            if "rate" in row or doctype in {"Purchase Order", "Purchase Invoice", "Sales Order", "Sales Invoice", "Quotation"}:
                row["rate"] = rate
                row["amount"] = round(qty * rate, 2)
            new_rows.append(row)
        hydrated["items"] = new_rows
        return hydrated

    def _apply_natural_draft_updates(self, data: dict[str, Any], message: str) -> dict[str, Any]:
        rows = data.get("items")
        if not isinstance(rows, list) or not rows:
            return {"matched": False, "applied": False, "changes": [], "errors": []}
        updates = self._parse_row_updates(message)
        if not updates:
            return {"matched": False, "applied": False, "changes": [], "errors": []}
        changes: list[dict[str, Any]] = []
        errors: list[str] = []
        planned: list[tuple[int, dict[str, Any], dict[str, Any]]] = []
        used_indexes: set[int] = set()
        for update in updates:
            candidates = self._rank_rows_for_query(rows, str(update["query"]))
            candidates = [item for item in candidates if item[0] not in used_indexes]
            if not candidates or candidates[0][1] <= 0:
                errors.append(f"I could not match “{update['query']}” to an item row in the active draft.")
                continue
            if len(candidates) > 1 and candidates[0][1] == candidates[1][1]:
                errors.append(f"“{update['query']}” matches more than one row. Please be more specific.")
                continue
            index = candidates[0][0]
            used_indexes.add(index)
            planned.append((index, update, dict(rows[index])))
        if errors:
            return {"matched": True, "applied": False, "changes": [], "errors": errors}
        for index, update, before in planned:
            row = rows[index]
            field = str(update["field"])
            value = update["value"]
            row[field] = value
            if field == "rate":
                row["rate_source"] = "user"
            qty = self._to_float(row.get("qty"), 1)
            rate = self._to_float(row.get("rate"), 0)
            if field in {"qty", "rate"}:
                row["qty"] = qty
                row["rate"] = rate
                row["amount"] = round(qty * rate, 2)
            changes.append({
                "table_field": "items",
                "row_id": row.get("row_id") or f"row-{index+1}",
                "fieldname": field,
                "old_value": before.get(field),
                "new_value": value,
                "label": self._row_label(row),
            })
        return {"matched": True, "applied": True, "changes": changes, "errors": []}

    @staticmethod
    def _parse_row_updates(message: str) -> list[dict[str, Any]]:
        text = " ".join(message.strip().split())
        lowered = text.lower()
        if not re.search(r"\b(update|set|change|correct|edit)\b", lowered):
            return []
        field = None
        if re.search(r"\b(rate|price|cost)\b", lowered):
            field = "rate"
        elif re.search(r"\b(qty|quantity|units?|pcs|pieces)\b", lowered):
            field = "qty"
        elif re.search(r"\buom\b", lowered):
            field = "uom"
        if not field:
            return []
        body = re.sub(r"^(?:please\s+)?(?:update|set|change|correct|edit)\s+", "", text, flags=re.I).strip()
        body = re.sub(rf"^(?:the\s+)?{field}\s+(?:for\s+)?", "", body, flags=re.I).strip()
        segments = [segment.strip(" ,.;") for segment in re.split(r"\s+(?:and|&)\s+|[,;]+", body) if segment.strip(" ,.;")]
        updates: list[dict[str, Any]] = []
        for segment in segments:
            match = re.search(r"(.+?)\s+(?:rate|price|cost|qty|quantity|uom)?\s*(?:to|as|=|at)?\s*([A-Za-z]*\s*[-+]?\d+(?:,\d{3})*(?:\.\d+)?|[A-Za-z][A-Za-z0-9 -]{0,20})$", segment, re.I)
            if not match:
                continue
            query = re.sub(r"\b(rate|price|cost|qty|quantity|uom|for|item|row)\b", " ", match.group(1), flags=re.I)
            query = " ".join(query.strip().split())
            raw_value = match.group(2).strip()
            if field in {"rate", "qty"}:
                number_match = re.search(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?", raw_value)
                if not number_match or not query:
                    continue
                value: Any = float(number_match.group(0).replace(",", ""))
            else:
                value = raw_value
            updates.append({"field": field, "query": query, "value": value, "source_text": segment})
        return updates

    @staticmethod
    def _rank_rows_for_query(rows: list[dict[str, Any]], query: str) -> list[tuple[int, int]]:
        query_norm = ChatService._normalize_match_text(query)
        query_tokens = {token for token in query_norm.split() if token}
        ranked: list[tuple[int, int]] = []
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            haystack = ChatService._normalize_match_text(" ".join(str(row.get(field) or "") for field in ("item_code", "item_name", "description", "source_text", "item_query")))
            tokens = set(haystack.split())
            score = 0
            if query_norm and query_norm in haystack:
                score += 10
            score += sum(3 for token in query_tokens if token in tokens)
            if "ac" in query_tokens and any(token in tokens for token in {"ac", "air", "conditioner", "split", "midea"}):
                score += 8
            if "oven" in query_tokens and "oven" in tokens:
                score += 8
            ranked.append((index, score))
        ranked.sort(key=lambda item: item[1], reverse=True)
        return ranked

    @staticmethod
    def _normalize_match_text(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()

    @staticmethod
    def _row_label(row: dict[str, Any]) -> str:
        return str(row.get("item_name") or row.get("item_code") or row.get("description") or row.get("source_text") or "row")

    @staticmethod
    def _draft_totals(data: dict[str, Any]) -> dict[str, Any]:
        rows = data.get("items") if isinstance(data, dict) else []
        if not isinstance(rows, list):
            return {}
        total = 0.0
        for row in rows:
            if not isinstance(row, dict):
                continue
            qty = ChatService._to_float(row.get("qty"), 0)
            rate = ChatService._to_float(row.get("rate"), 0)
            amount = ChatService._to_float(row.get("amount"), qty * rate)
            total += amount
        return {"net_total": round(total, 2), "grand_total": round(total, 2)}

    @staticmethod
    def _to_float(value: Any, default: float = 0) -> float:
        try:
            return float(str(value).replace(",", "").strip())
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _invalidate_pending_confirmation(pending: dict[str, Any]) -> None:
        confirmation_id = str(pending.get("confirmation_id") or "")
        if confirmation_id:
            confirmation_store.cancel(confirmation_id)

    @staticmethod
    def _draft_edit_error_response(conversation_id: str, doctype: str, errors: list[str]) -> AssistantChatResponse:
        message_id = new_id("msg")
        summary = "I understood that you want to edit the active draft, but I could not safely apply the change. " + " ".join(errors)
        return AssistantChatResponse(conversation_id=conversation_id, message_id=message_id, intent="draft_edit_failed", parts=[TextPart(content=summary)], permission=PermissionMeta(allowed=True, risk_level="low", confirmation_required=True), id=message_id, content=summary, created_at=utc_now())

    @staticmethod
    def _is_proceed_command(text: str) -> bool:
        return bool(re.search(r"\b(proceed|continue|use selected|prepare preview|review draft)\b", text))

    @staticmethod
    def _remove_matching_row(data: dict[str, Any], message: str) -> bool:
        match = re.search(r"\bremove\s+(?:the\s+)?(.+)$", message, re.I)
        if not match:
            return False
        needle = re.sub(r"\b(item|items?)\b", "", match.group(1), flags=re.I).strip().lower()
        rows = data.get("items")
        if not isinstance(rows, list) or not needle:
            return False
        before = len(rows)
        data["items"] = [row for row in rows if not (isinstance(row, dict) and needle in str(row.get("source_text") or row.get("item_query") or row.get("description") or "").lower())]
        return len(data["items"]) != before

    @staticmethod
    def _apply_short_correction(data: dict[str, Any], message: str) -> bool:
        text = " ".join(message.strip().split())
        if not text or len(text.split()) > 6 or re.search(r"\b(create|draft|show|list|proceed|continue|remove|supplier|customer|qty)\b", text, re.I):
            return False
        rows = data.get("items")
        if not isinstance(rows, list):
            return False
        unresolved = [row for row in rows if isinstance(row, dict) and not row.get("item_code")]
        if not unresolved:
            return False
        target = unresolved[-1]
        lowered = text.lower()
        for row in unresolved:
            original = str(row.get("item_query") or row.get("source_text") or "").lower()
            if any(token in lowered for token in original.split() if len(token) > 2) or any(token in original for token in lowered.split() if len(token) > 2):
                target = row
                break
        target["item_query"] = text
        target["source_text"] = text
        return True

    @staticmethod
    def _warehouse_requirement(data: dict[str, Any]) -> list[str]:
        rows = data.get("items")
        if not isinstance(rows, list):
            return []
        return [
            str(row.get("row_id") or f"row-{index+1}")
            for index, row in enumerate(rows)
            if isinstance(row, dict) and row.get("item_code") and not row.get("warehouse")
        ]

    @staticmethod
    def _warehouse_options_requested(text: str) -> bool:
        return "warehouse" in text and bool(re.search(r"\b(show|list|available|which|options?)\b", text))

    def _evaluate_draft_readiness(self, doctype: str, data: dict[str, Any]) -> dict[str, Any]:
        blocking: list[dict[str, Any]] = []
        rows = data.get("items")
        if isinstance(rows, list):
            for index, row in enumerate(rows):
                if not isinstance(row, dict):
                    continue
                row_id = str(row.get("row_id") or f"row-{index+1}")
                if not row.get("item_code"):
                    blocking.append({"scope": "child_row", "table_field": "items", "row_id": row_id, "fieldname": "item_code", "reason": "Item is unresolved"})
                if float(row.get("qty") or 0) <= 0:
                    blocking.append({"scope": "child_row", "table_field": "items", "row_id": row_id, "fieldname": "qty", "reason": "Quantity must be greater than zero"})
                if doctype in {"Purchase Order"} and row.get("item_code") and not row.get("warehouse"):
                    blocking.append({"scope": "child_row", "table_field": "items", "row_id": row_id, "fieldname": "warehouse", "reason": "Warehouse is required for this item row"})
        return {"ready": not blocking, "blocking_requirements": blocking}

    async def _draft_warehouse_options_response(self, conversation_id: str, doctype: str, data: dict[str, Any], cookies: dict | None, prompt: str) -> AssistantChatResponse:
        row_ids = self._warehouse_requirement(data)
        query = self._warehouse_query(prompt)
        options = await self._warehouse_options(data, cookies, query)
        message_id = new_id("msg")
        summary = "A warehouse is required for the selected stock items. Choose a valid leaf warehouse before I prepare the draft preview."
        part = DraftFieldOptionsPart(
            draft_session_id=conversation_id,
            doctype=doctype,
            fieldname="warehouse",
            label="Warehouse",
            table_field="items",
            row_ids=row_ids,
            message="Choose a warehouse for the Purchase Order items.",
            options=options,
        )
        await self.repository.save_pending_draft(conversation_id, {"doctype": doctype, "operation": "create", "data": data, "message_id": message_id, "status": "awaiting_warehouse"})
        return AssistantChatResponse(conversation_id=conversation_id, message_id=message_id, intent="draft_field_options", parts=[TextPart(content=summary), part], permission=PermissionMeta(allowed=True, risk_level="low", confirmation_required=True), id=message_id, content=summary, created_at=utc_now())

    async def _try_apply_warehouse_from_text(self, data: dict[str, Any], message: str, cookies: dict | None) -> bool:
        query = self._warehouse_query(message)
        if not query:
            return False
        options = await self._warehouse_options(data, cookies, query)
        valid = [option for option in options if not option.disabled and option.value.lower() == query.lower()]
        if not valid:
            valid = [option for option in options if not option.disabled]
        if not valid:
            return False
        selected = valid[0].value
        rows = data.get("items")
        if not isinstance(rows, list):
            return False
        for row in rows:
            if isinstance(row, dict) and row.get("item_code") and not row.get("warehouse"):
                row["warehouse"] = selected
        data["set_warehouse"] = selected
        return True

    @staticmethod
    def _warehouse_query(message: str) -> str:
        text = " ".join(message.strip().split())
        text = re.sub(r"^(?:show|list|which|available|use|select|set)\s+(?:me\s+)?", "", text, flags=re.I).strip()
        text = re.sub(r"^(?:warehouse|warehouses)\s*(?:list|options?)?\s*", "", text, flags=re.I).strip()
        text = re.sub(r"\b(?:for\s+all\s+items?|for\s+the\s+draft|as\s+warehouse|warehouse)\b", "", text, flags=re.I).strip(" .:-")
        if re.search(r"\b(list|available|options?)\b", text, re.I):
            return ""
        return text

    async def _warehouse_options(self, data: dict[str, Any], cookies: dict | None, query: str = "") -> list[DraftFieldOption]:
        fields = ["name", "warehouse_name", "company", "is_group", "disabled"]
        try:
            records = (await entity_resolution_service.erp.list_records("Warehouse", {}, fields, 100, cookies=cookies)).records
        except Exception:
            records = []
        company = str(data.get("company") or "").strip().lower()
        normalized_query = query.strip().lower()
        options: list[DraftFieldOption] = []
        for row in records:
            name = str(row.get("name") or "")
            label = str(row.get("warehouse_name") or name)
            is_group = bool(row.get("is_group"))
            disabled = bool(row.get("disabled"))
            row_company = str(row.get("company") or "")
            if normalized_query and normalized_query not in name.lower() and normalized_query not in label.lower():
                continue
            if company and row_company and row_company.lower() != company:
                continue
            invalid = is_group or disabled
            options.append(DraftFieldOption(value=name, label=label if label == name else f"{name} — {label}", description="Leaf warehouse" if not invalid else "Cannot be used for transaction rows", disabled=invalid, reason="Group warehouses cannot be used on item rows." if is_group else "Warehouse is disabled." if disabled else None, metadata={"company": row_company, "is_group": is_group, "disabled": disabled}))
        return options[:20]

    async def _remember_pending_draft(self, response: AssistantChatResponse) -> None:
        missing = next((part for part in response.parts if isinstance(part, MissingFieldsPart)), None)
        preview = next((part for part in response.parts if isinstance(part, RecordPreviewPart)), None)
        confirmation = next((part for part in response.parts if isinstance(part, ConfirmationPart)), None)
        field_options = next((part for part in response.parts if isinstance(part, DraftFieldOptionsPart)), None)
        if missing:
            await self.repository.save_pending_draft(response.conversation_id, {"doctype": missing.doctype, "operation": missing.operation, "record_name": missing.record_name, "data": missing.collected_data, "message_id": response.message_id})
        elif field_options:
            current = await self.repository.get_pending_draft(response.conversation_id)
            if current:
                current["message_id"] = response.message_id
                current["status"] = f"awaiting_{field_options.fieldname}"
                await self.repository.save_pending_draft(response.conversation_id, current)
        elif preview:
            current = await self.repository.get_pending_draft(response.conversation_id) or {}
            version = int(current.get("version") or 0) + 1
            preview.draft_session_id = response.conversation_id
            preview.draft_version = version
            if preview.after_data.get("items"):
                preview.totals = self._draft_totals(preview.after_data)
            await self.repository.save_pending_draft(response.conversation_id, {
                "doctype": preview.doctype,
                "operation": preview.operation,
                "record_name": preview.record_name,
                "data": preview.after_data,
                "message_id": response.message_id,
                "status": "awaiting_confirmation",
                "confirmation_id": confirmation.confirmation_id if confirmation else None,
                "version": version,
            })

    async def _resolve_report_followup(self, request: ChatMessageRequest, conversation_id: str) -> dict[str, Any] | None:
        action = request.structured_action or {}
        text = request.message.lower()
        has_structured_transform = action.get("action") == "transform_report" or action.get("action_type") == "transform_report"
        has_followup_language = any(
            phrase in text
            for phrase in (
                "this result",
                "same filters",
                "show as chart",
                "as a chart",
                "summarize it",
                "summarize this",
                "group it",
                "group by",
                "monthly trend",
                "drill down",
                "show details",
                "show source rows",
                "export it",
                "pin report",
                "pin to overview",
            )
        )
        if not has_structured_transform and not has_followup_language:
            return None
        result_id = str(action.get("result_id") or request.active_result_id or "") or None
        report_id = str(action.get("report_id") or request.active_report_id or "") or None
        context = await self.repository.get_result_context(conversation_id, result_id=result_id, report_id=report_id)
        if not context:
            context = await self.repository.get_latest_result_context(conversation_id)
        if not context:
            context = await self._result_context_from_messages(conversation_id, result_id)
        if not context:
            return {
                "intent": "clarification_required",
                "operation": "clarify",
                "context": {},
                "reason": "No active report result is available for this follow-up.",
            }
        operation = str(action.get("operation") or "").lower()
        if not operation:
            if "chart" in text or "visual" in text or "summarize" in text:
                operation = "visualize"
            elif "group by customer" in text or "customer" in text and "group" in text:
                operation = "regroup"
                action["group_by"] = "customer"
            elif "monthly" in text or "month" in text:
                operation = "regroup"
                action["group_by"] = "month"
            elif "export" in text or "pdf" in text or "excel" in text:
                operation = "export"
            elif "pin" in text:
                operation = "pin"
            else:
                operation = "clarify"
        intent = {
            "visualize": "visualize_existing_report",
            "regroup": "regroup_existing_report",
            "export": "export_existing_report",
            "pin": "pin_existing_report",
        }.get(operation, "clarification_required")
        return {"intent": intent, "operation": operation, "action": action, "context": context}

    async def _result_context_from_messages(self, conversation_id: str, result_id: str | None = None) -> dict[str, Any] | None:
        messages = await self.repository.get_messages(conversation_id)
        for message in reversed(messages):
            if message.role != "assistant":
                continue
            table = next((part for part in message.parts if part.get("type") == "table"), None)
            chart = next((part for part in message.parts if part.get("type") == "chart"), None)
            if not table and not chart:
                continue
            candidate_id = (chart or {}).get("result_id") or (chart or {}).get("resultId") or (table or {}).get("result_id") or (table or {}).get("resultId")
            if result_id and candidate_id and result_id != candidate_id:
                continue
            rows = (table or {}).get("rows") or (chart or {}).get("data") or []
            source = message.source
            columns = [column.get("key") for column in (table or {}).get("columns", []) if column.get("key")]
            if not columns and rows:
                columns = list(rows[0].keys())
            return {
                "report_id": ((chart or {}).get("config") or (table or {}).get("config") or {}).get("report_id") or new_id("report"),
                "result_id": candidate_id or new_id("res"),
                "conversation_id": conversation_id,
                "message_id": message.id,
                "intent": message.intent,
                "doctype": source.doctype if source else None,
                "report_name": source.report_name if source else None,
                "source_type": source.source_type if source else None,
                "source_name": source.source_name if source else None,
                "title": (chart or {}).get("title") or (table or {}).get("title") or message.content[:80],
                "columns": columns,
                "filters": source.filters if source and source.filters else {},
                "rows": rows,
                "chart": chart,
                "row_count": source.record_count if source and source.record_count is not None else len(rows),
                "created_at": message.created_at.isoformat(),
            }
        return None

    async def _handle_report_followup(self, followup: dict[str, Any], conversation_id: str, cookies: dict | None, user: str) -> AssistantChatResponse:
        if followup["intent"] == "visualize_existing_report":
            return self._visualize_existing_report(conversation_id, followup["context"], followup.get("action") or {})
        if followup["intent"] == "regroup_existing_report":
            return await self._regroup_existing_report(conversation_id, followup["context"], followup.get("action") or {}, cookies, user)
        return self._unsupported_response(conversation_id, followup.get("reason"))

    def _visualize_existing_report(self, conversation_id: str, context: dict[str, Any], action: dict[str, Any]) -> AssistantChatResponse:
        rows = list(context.get("rows") or [])
        chart = self._chart_from_result_context(context, rows, action)
        message_id = new_id("msg")
        summary = f"Here is {chart.title.lower()} using the same filters."
        return AssistantChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            intent="chart_result",
            parts=[
                TextPart(content=summary),
                ToolCallPart(tool_name="transform_report", status="success", input_summary=context.get("title") or context.get("source_name"), output_summary=f"{len(chart.data)} chart points"),
                chart,
            ],
            source=SourceMeta(
                source_type="doctype" if context.get("doctype") else "report",
                source_name=context.get("source_name") or context.get("doctype") or context.get("report_name") or "Report",
                record_count=len(chart.data),
                filters=context.get("filters") or {},
                doctype=context.get("doctype"),
                report_name=context.get("report_name"),
                fields=context.get("columns") or [],
            ),
            permission=PermissionMeta(allowed=True, risk_level="low"),
            suggested_actions=self._result_actions(chart.result_id, context),
            id=message_id,
            content=summary,
            created_at=utc_now(),
        )

    async def _regroup_existing_report(self, conversation_id: str, context: dict[str, Any], action: dict[str, Any], cookies: dict | None, user: str) -> AssistantChatResponse:
        group_by = str(action.get("group_by") or "").lower()
        doctype = context.get("doctype") or context.get("source_name")
        if not doctype:
            return self._unsupported_response(conversation_id, "I understood that you want to regroup the report, but I could not find the source DocType.")
        if group_by in {"customer", "supplier"}:
            metrics = [AggregationMetric(field="grand_total", function="sum")]
            if any("outstanding_amount" in row for row in context.get("rows") or []):
                metrics.append(AggregationMetric(field="outstanding_amount", function="sum"))
            plan = AggregationPlan(
                enabled=True,
                source_name=str(doctype),
                filters=context.get("filters") or {},
                fields=[group_by],
                group_by=[group_by],
                metrics=metrics,
                chart_type="bar",
                chart_title=f"{doctype} by {group_by.title()}",
                limit=50,
            )
        elif group_by in {"month", "monthly"}:
            plan = AggregationPlan(
                enabled=True,
                source_name=str(doctype),
                filters=context.get("filters") or {},
                fields=["posting_date"],
                group_by=[],
                metrics=[AggregationMetric(field="grand_total", function="sum")],
                time_field="posting_date",
                time_grain="month",
                chart_type="bar",
                chart_title=f"Monthly {doctype} Trend",
                limit=24,
            )
        else:
            return self._unsupported_response(conversation_id, "I understood that you want to regroup the report, but I need a supported grouping such as customer or month.")
        result = await self.aggregation_agent.service.run_aggregation(plan, cookies, user, conversation_id)
        result_id = new_id("res")
        chart = normalize_chart_data(result.chart or {})
        message_id = new_id("msg")
        title = result.plan.chart_title or f"{doctype} Summary"
        parts: list = [
            TextPart(content=result.summary),
            ToolCallPart(tool_name="transform_report", status="success", input_summary=f"group_by={group_by}", output_summary=f"{len(result.rows)} grouped rows"),
            build_table_part(title, result.rows, result_id=result_id, config={"report_id": context.get("report_id"), "filters": result.source.get("filters") or {}, "group_by": group_by}),
        ]
        if chart:
            parts.append(ChartPart(result_id=result_id, source_type="analytics", source_name=str(doctype), title=chart.get("title") or title, chart_type=self._safe_chart_type(chart.get("chart_type") or "bar"), data=chart.get("data") or result.rows, x_key=chart.get("x_key") or "period", y_key=chart.get("y_key") or "grand_total_sum", config={"report_id": context.get("report_id"), "filters": result.source.get("filters") or {}, "group_by": group_by}, available_actions=["export_excel", "generate_pdf", "pin", "change_chart_type", "refine_filters"]))
        return AssistantChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            intent="report_result",
            parts=parts,
            source=SourceMeta(source_type="doctype", source_name=str(doctype), record_count=len(result.rows), filters=result.source.get("filters") or {}, doctype=str(doctype)),
            permission=PermissionMeta.model_validate(result.permission or {"allowed": True, "risk_level": "low"}),
            suggested_actions=self._result_actions(result_id, context),
            id=message_id,
            content=result.summary,
            created_at=utc_now(),
        )

    def _chart_from_result_context(self, context: dict[str, Any], rows: list[dict[str, Any]], action: dict[str, Any]) -> ChartPart:
        existing_chart = dict(context.get("chart") or {})
        if existing_chart.get("data"):
            chart = normalize_chart_data({**existing_chart, "chart_type": action.get("chart_type") or existing_chart.get("chart_type") or existing_chart.get("type") or "bar"})
            return ChartPart(
                result_id=new_id("res"),
                source_type="analytics",
                source_name=context.get("source_name"),
                title=chart.get("title") or context.get("title") or "Report Chart",
                chart_type=self._safe_chart_type(chart.get("chart_type") or "bar"),
                data=chart.get("data") or [],
                x_key=chart.get("x_key") or chart.get("name_key") or self._first_dimension(rows),
                y_key=chart.get("y_key") or chart.get("value_key") or self._first_metric(rows),
                config={**(chart.get("config") or {}), "report_id": context.get("report_id"), "parent_result_id": context.get("result_id"), "filters": context.get("filters") or {}},
                available_actions=["export_excel", "generate_pdf", "pin", "change_chart_type", "refine_filters"],
            )
        x_key = self._first_dimension(rows) or "period"
        y_key = self._first_metric(rows) or "value"
        chart_type = "line" if self._looks_temporal(rows, x_key) else "bar"
        chart = normalize_chart_data({"chart_type": chart_type, "title": context.get("title") or context.get("source_name") or "Report Chart", "x_key": x_key, "y_key": y_key, "data": rows})
        return ChartPart(
            result_id=new_id("res"),
            source_type="analytics",
            source_name=context.get("source_name"),
            title=chart.get("title") or "Report Chart",
            chart_type=self._safe_chart_type(chart.get("chart_type") or chart_type),
            data=chart.get("data") or [],
            x_key=x_key,
            y_key=y_key,
            config={"report_id": context.get("report_id"), "parent_result_id": context.get("result_id"), "filters": context.get("filters") or {}},
            available_actions=["export_excel", "generate_pdf", "pin", "change_chart_type", "refine_filters"],
        )

    async def _remember_report_context(self, response: AssistantChatResponse, intent: IntentResult, request: ChatMessageRequest) -> None:
        table = next((part for part in response.parts if isinstance(part, TablePart)), None)
        chart = next((part for part in response.parts if isinstance(part, ChartPart)), None)
        if not table and not chart:
            return
        result_id = (chart.result_id if chart else None) or (table.result_id if table else None) or new_id("res")
        report_id = None
        if chart and chart.config.get("report_id"):
            report_id = str(chart.config["report_id"])
        elif table and table.config.get("report_id"):
            report_id = str(table.config["report_id"])
        report_id = report_id or new_id("report")
        if table and not table.result_id:
            table.result_id = result_id
        if chart and not chart.result_id:
            chart.result_id = result_id
        if table:
            table.config = {**table.config, "report_id": report_id, "result_id": result_id}
        if chart:
            chart.config = {**chart.config, "report_id": report_id, "result_id": result_id}
        rows = list((table.rows if table else None) or (chart.data if chart else []) or [])
        context = {
            "report_id": report_id,
            "result_id": result_id,
            "conversation_id": response.conversation_id,
            "message_id": response.message_id,
            "intent": response.intent,
            "analytics_key": (chart.config or {}).get("analytics_key") if chart else getattr(intent, "analytics_key", None),
            "doctype": response.source.doctype if response.source else intent.doctype,
            "report_name": response.source.report_name if response.source else intent.report_name,
            "source_type": response.source.source_type if response.source else None,
            "source_name": response.source.source_name if response.source else (intent.doctype or intent.report_name),
            "title": (chart.title if chart else None) or (table.title if table else None) or response.content[:80],
            "columns": [column.key for column in table.columns] if table else list(rows[0].keys()) if rows else [],
            "filters": (response.source.filters if response.source and response.source.filters else None) or request.current_filters or {},
            "rows": rows,
            "chart": chart.model_dump(mode="json") if chart else None,
            "row_count": response.source.record_count if response.source and response.source.record_count is not None else len(rows),
            "created_at": utc_now().isoformat(),
        }
        await self.repository.save_result_context(response.conversation_id, context)

    @staticmethod
    def _result_actions(result_id: str | None, context: dict[str, Any]) -> list[SuggestedAction]:
        payload = {
            "action": "transform_report",
            "report_id": context.get("report_id"),
            "result_id": result_id or context.get("result_id"),
            "preserve_filters": True,
            "preserve_grouping": True,
            "source": "generated_action",
        }
        return [
            SuggestedAction(label="Export Excel", action_type="export_excel", payload={**payload, "file_format": "xlsx"}),
            SuggestedAction(label="Generate PDF", action_type="generate_pdf", payload={**payload, "file_format": "pdf"}),
            SuggestedAction(label="Pin to Overview", action_type="pin_to_overview", payload=payload),
            SuggestedAction(label="Refine Filters", action_type="refine_filters", payload=payload),
        ]

    @staticmethod
    def _first_dimension(rows: list[dict[str, Any]]) -> str | None:
        if not rows:
            return None
        preferred = ("period", "month", "posting_date", "transaction_date", "customer", "supplier", "status")
        keys = list(rows[0].keys())
        return next((key for key in preferred if key in keys), next((key for key in keys if not isinstance(rows[0].get(key), (int, float))), None))

    @staticmethod
    def _first_metric(rows: list[dict[str, Any]]) -> str | None:
        if not rows:
            return None
        preferred = ("grand_total_sum", "sales_total", "purchase_total", "outstanding_amount_sum", "amount", "value")
        keys = list(rows[0].keys())
        return next((key for key in preferred if key in keys), next((key for key in keys if isinstance(rows[0].get(key), (int, float)) and not isinstance(rows[0].get(key), bool)), None))

    @staticmethod
    def _looks_temporal(rows: list[dict[str, Any]], x_key: str | None) -> bool:
        if not rows or not x_key:
            return False
        return x_key in {"period", "month", "posting_date", "transaction_date"} or any("-" in str(row.get(x_key, "")) for row in rows[:3])

    @staticmethod
    def _safe_chart_type(value: str) -> str:
        return value if value in {"bar", "line", "pie", "donut", "area"} else "bar"

    async def _persist_response(self, response: AssistantChatResponse) -> None:
        await self.repository.save_message(
            ChatMessage(
                id=response.message_id,
                conversation_id=response.conversation_id,
                role="assistant",
                content=response.content,
                created_at=response.created_at,
                parts=[part.model_dump(mode="json") for part in response.parts],
                intent=response.intent,
                source=response.source,
                permission=response.permission,
                suggested_actions=response.suggested_actions,
                suggestions=response.suggestions,
                extraction=response.extraction,
            )
        )
        for part in response.parts:
            if isinstance(part, ToolCallPart):
                await self.repository.save_tool_call({
                    "id": new_id("tool"),
                    "conversation_id": response.conversation_id,
                    "tool_name": part.tool_name,
                    "status": part.status,
                    "input_summary": part.input_summary,
                    "output_summary": part.output_summary,
                })

    async def _audit(
        self,
        user: str,
        prompt: str,
        intent: IntentResult,
        response: AssistantChatResponse,
        safety: SafetyResult,
    ) -> None:
        tool_part = next((part for part in response.parts if isinstance(part, ToolCallPart)), None)
        permission = response.permission
        if intent.intent.startswith("workflow_"): audit_action = intent.intent
        elif intent.intent == "blocked_write": audit_action = "crud_blocked_action"
        elif intent.intent == "crud_create": audit_action = "crud_prepare_create"
        elif intent.intent == "crud_update": audit_action = "crud_prepare_update"
        elif intent.intent == "report_composer": audit_action = "report_composer_run_completed"
        else: audit_action = "read_only_chat_tool" if tool_part else "chat_safety_response"
        await log_audit_event(AuditEvent(
            user=user or "unknown",
            conversation_id=response.conversation_id,
            action=audit_action,
            agent_name="workflow_agent" if intent.intent.startswith("workflow_") else ("crud_agent" if intent.intent in {"crud_create", "crud_update"} else ("report_composer_agent" if intent.intent == "report_composer" else ("file_generation_agent" if intent.intent == "generate_file" else ("report_agent" if intent.intent == "run_report" else "erp_data_agent")))),
            tool_name=tool_part.tool_name if tool_part else None,
            doctype=intent.doctype,
            record_name=intent.record_name,
            report_name=intent.report_name,
            allowed=bool(safety.allowed and (permission.allowed if permission else True)),
            risk_level=permission.risk_level if permission else safety.risk_level,
            input_summary=tool_part.input_summary if tool_part else intent.intent,
            output_summary=tool_part.output_summary if tool_part else response.content[:200],
            prompt=self._audit_prompt(prompt, intent),
            intent=intent.intent,
            filters=intent.filters or {},
            record_count=response.source.record_count if response.source else 0,
            provider=intent.llm_provider,
            model=intent.llm_model,
            extraction_method=intent.extraction_method,
            confidence=intent.llm_confidence or intent.confidence,
            privacy_allowed=intent.privacy_allowed if intent.privacy_checked else None,
            erp_data_sent=False,
            fallback_used=intent.fallback_used,
        ))

    async def _attach_suggestions(
        self,
        response: AssistantChatResponse,
        previous_prompt: str,
        intent: IntentResult,
        cookies: dict | None,
        user: str,
        user_roles: list[str],
    ) -> None:
        context = self.suggestion_context.from_assistant_result(
            response,
            previous_prompt=previous_prompt,
            conversation_id=response.conversation_id,
            message_id=response.message_id,
        )
        if intent.query_plan and intent.query_plan.aggregation:
            context.analytics_key = intent.query_plan.aggregation.chart_title
        generated = await self.suggestions.generate_suggestions(context, user_roles, cookies, user)
        response.suggestions = generated.suggestions

    @staticmethod
    def _blocked_response(
        conversation_id: str,
        intent: IntentResult,
        safety: SafetyResult,
    ) -> AssistantChatResponse:
        summary = safety.reason or "This request is blocked by the read-only safety policy."
        message_id = new_id("msg")
        response_intent = "blocked_write" if intent.intent == "blocked_write" else ("write_blocked" if intent.write_requested else "blocked")
        return AssistantChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            intent=response_intent,
            parts=[TextPart(content=summary), ToolCallPart(tool_name="safety_guard", status="error", input_summary=intent.intent, output_summary="Action blocked")],
            permission=PermissionMeta(allowed=False, risk_level="high", reason=summary),
            suggested_actions=[
                SuggestedAction(label="View related records", action_type="view_related"),
                SuggestedAction(label="Open module", action_type="open_module"),
                SuggestedAction(label="Prepare a safe draft", action_type="prepare_later", disabled=True, reason="Only allowlisted draft creates and safe updates are enabled."),
            ],
            id=message_id,
            content=summary,
            created_at=utc_now(),
        )

    @staticmethod
    def _unsupported_response(conversation_id: str, message: str | None = None) -> AssistantChatResponse:
        message_id = new_id("msg")
        content = message or CLARIFICATION_MESSAGE
        return AssistantChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            intent="clarification_required",
            parts=[TextPart(content=content)],
            suggested_actions=[
                SuggestedAction(label="Show this result as a bar chart", action_type="prompt", reason="Show this result as a bar chart"),
                SuggestedAction(label="Group this report by customer", action_type="prompt", reason="Group this report by customer"),
                SuggestedAction(label="Show the underlying invoices", action_type="prompt", reason="Show the underlying invoices"),
            ],
            id=message_id,
            content=content,
            created_at=utc_now(),
        )

    @staticmethod
    def _conversation_title(message: str) -> str:
        clean = " ".join(message.split())
        return clean[:80] or "New command"

    @staticmethod
    def _safe_prompt(prompt: str) -> str:
        lowered = prompt.lower()
        if any(term in lowered for term in ("password", "api key", "api secret", "token", "otp")):
            return "[REDACTED SENSITIVE PROMPT]"
        return prompt[:300]

    @classmethod
    def _audit_prompt(cls, prompt: str, intent: IntentResult) -> str | None:
        if intent.intent in {"crud_create", "crud_update"}:
            return f"{intent.operation} {intent.doctype}; fields={','.join((intent.data or {}).keys())}"
        if not (settings.llm_log_prompts or settings.llm_log_redacted_prompts):
            return None
        return cls._safe_prompt(prompt)

    @staticmethod
    def _attach_previous_result(intent: IntentResult, messages: list[ChatMessage]) -> None:
        for message in reversed(messages[:-1]):
            table = next((part for part in message.parts if part.get("type") == "table"), None)
            chart = next((part for part in message.parts if part.get("type") == "chart"), None)
            if table or chart:
                intent.rows = (table or {}).get("rows") or []
                intent.chart_config = chart
                intent.source_name = message.source.source_name if message.source else "Previous chat result"
                intent.filters = message.source.filters if message.source else {}
                return

    @staticmethod
    def _safe_action_summary(action: dict[str, Any] | None) -> dict[str, Any]:
        if not action:
            return {}
        allowed = {"action", "action_type", "operation", "visualization", "group_by", "report_id", "result_id", "preserve_filters", "preserve_grouping", "source", "file_format"}
        return {key: value for key, value in action.items() if key in allowed}


chat_service = ChatService()
