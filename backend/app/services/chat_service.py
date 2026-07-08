from app.agents.erp_data_agent import ERPDataAgent
from app.agents.aggregation_agent import AggregationAgent
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
    TextPart,
    ToolCallPart,
)
from app.schemas.crud import CancelCrudResponse, ConfirmCrudRequest, ConfirmCrudResponse, ContinueCrudRequest
from app.schemas.dashboard import DashboardWidgetSource, PinChatResultRequest, PinChatResultResponse
from app.services.dashboard_service import DashboardService, dashboard_service
from app.services.conversation_repository import InMemoryConversationRepository
from app.services.suggestion_service import SuggestionService, suggestion_service
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.suggestion_context_builder import SuggestionContextBuilder

READ_ONLY_FALLBACK = (
    "I can help with ERPNext queries such as customers, suppliers, items, invoices, orders, "
    "stock balance, receivables, payables, and general ledger. I can also prepare allowlisted "
    "draft records or safe field updates for your confirmation."
)


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

        intent = await self.router.classify(request.message, request.module_context, user, conversation.id)
        intent.conversation_id = conversation.id
        if intent.intent == "generate_file" and intent.source_type == "chat_result":
            self._attach_previous_result(intent, await self.repository.get_messages(conversation.id))
        safety = await self.safety.validate(intent)

        if not safety.allowed:
            response = self._blocked_response(conversation.id, intent, safety)
        elif intent.intent in {"workflow_list_pending", "workflow_get_detail", "workflow_apply_action"}:
            response = await self.workflow_agent.handle(intent, cookies, user)
        elif intent.intent == "run_report":
            response = await self.report_agent.handle(intent, cookies)
        elif intent.intent == "generate_file":
            response = await self.file_agent.handle(intent, cookies, user)
        elif intent.intent in {"crud_create", "crud_update"}:
            response = await self.crud_agent.handle(intent, cookies, user)
        elif intent.intent == "report_composer":
            response = await self.report_composer_agent.handle(intent, cookies, user)
        elif intent.intent == "pin_to_dashboard":
            response = await self._pin_intent(intent, cookies, user)
        elif intent.aggregation and intent.aggregation.enabled and intent.query_plan:
            response = await self.aggregation_agent.handle(intent.query_plan, cookies, user, conversation.id)
        elif intent.intent in {"list_records", "get_record", "summary_query", "chart_query", "write_blocked"}:
            response = await self.erp_agent.handle(intent, cookies)
        else:
            response = self._unsupported_response(conversation.id)

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
        await self._attach_suggestions(response, request.message, intent, cookies, user, user_roles or [])
        await self._persist_response(response)
        await self._audit(user, request.message, intent, response, safety)
        return response

    async def continue_crud(self, request: ContinueCrudRequest, cookies: dict | None = None, user: str = "unknown") -> AssistantChatResponse:
        intent = IntentResult(
            intent="crud_create" if request.operation == "create" else "crud_update",
            operation=request.operation,
            doctype=request.doctype,
            record_name=request.record_name,
            data=request.data,
            conversation_id=request.conversation_id,
            raw_prompt=f"continue {request.operation} {request.doctype}",
            confidence=1,
        )
        response = await self.crud_agent.handle(intent, cookies, user)
        await self._persist_response(response)
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
            return self._unsupported_response(intent.conversation_id or new_id("conv"))
        message_id=new_id("msg")
        source_type="report" if intent.report_name else "doctype"
        source_name=intent.report_name or intent.doctype or "ERPNext"
        source=DashboardWidgetSource(source_type=source_type,source_name=source_name,doctype=intent.doctype,report_name=intent.report_name,filters=intent.filters or {},fields=intent.fields)
        widget_type=intent.widget_type or "table"
        request=PinChatResultRequest(conversation_id=intent.conversation_id or new_id("conv"),message_id=message_id,title=f"{source_name} — Tinni",widget_type=widget_type,source=source)
        widget=await self.dashboards.pin_from_chat(request,cookies,user)
        summary=f"I pinned {widget.title} to Overview. Its data will refresh through your current ERPNext permissions."
        return AssistantChatResponse(conversation_id=request.conversation_id,message_id=message_id,intent="pin_to_dashboard",parts=[TextPart(content=summary),ToolCallPart(tool_name="pin_to_dashboard",status="success",input_summary=source_name,output_summary=f"Widget {widget.widget_id} created")],source=SourceMeta(source_type=source_type,source_name=source_name,filters=intent.filters or {},doctype=intent.doctype,report_name=intent.report_name,fields=intent.fields),permission=PermissionMeta(allowed=True,risk_level="medium"),suggested_actions=[SuggestedAction(label="Open Overview",action_type="open_overview")],id=message_id,content=summary,created_at=utc_now())

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
    def _unsupported_response(conversation_id: str) -> AssistantChatResponse:
        message_id = new_id("msg")
        return AssistantChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            intent="unsupported",
            parts=[TextPart(content=READ_ONLY_FALLBACK)],
            suggested_actions=[
                SuggestedAction(label="Show customers", action_type="prompt", reason="show customers"),
                SuggestedAction(label="Show sales invoices", action_type="prompt", reason="show sales invoices"),
                SuggestedAction(label="Show stock balance", action_type="prompt", reason="show stock balance"),
            ],
            id=message_id,
            content=READ_ONLY_FALLBACK,
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


chat_service = ChatService()
