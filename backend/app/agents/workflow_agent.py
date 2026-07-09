from __future__ import annotations

from app.agents.router_agent import IntentResult
from app.core.exceptions import AppError
from app.schemas.chat import AssistantChatResponse, ConfirmationPart, PermissionMeta, SourceMeta, SuggestedAction, TextPart, ToolCallPart
from app.services.workflow_service import WorkflowService
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.table_formatter import build_table_part


class WorkflowAgent:
    def __init__(self, service: WorkflowService | None = None):
        self.service = service or WorkflowService()

    async def handle(self, intent: IntentResult, cookies: dict | None = None, user: str = "unknown") -> AssistantChatResponse:
        conversation_id = intent.conversation_id or new_id("conv")
        if intent.intent == "workflow_list_pending":
            try:
                result = await self.service.list_pending_approvals(intent.doctype, cookies, intent.limit, user)
            except AppError as exc:
                summary = f"I understood that you want pending approvals, but I could not fetch them from ERPNext. {exc.message}"
                return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary), ToolCallPart(tool_name="workflow_pending_approvals", status="error", output_summary=exc.message)], SourceMeta(source_type="tool", source_name="ERPNext Workflow", record_count=0, filters={"doctype": intent.doctype} if intent.doctype else {}), PermissionMeta(allowed=False, reason=exc.message))
            rows = [doc.model_dump(mode="json") | {"actions": ", ".join(action.action for action in doc.available_actions)} for doc in result.documents]
            summary = "You do not have any documents pending for approval." if not rows else f"I found {len(rows)} document{'s' if len(rows) != 1 else ''} pending for your approval."
            return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary), ToolCallPart(tool_name="workflow_pending_approvals", status="success", output_summary=f"{len(rows)} documents"), build_table_part("Pending Approvals", rows)], SourceMeta(source_type="tool", source_name="ERPNext Workflow", record_count=len(rows), filters=result.filters))

        if intent.intent == "workflow_get_detail":
            if not intent.doctype or not intent.record_name:
                return self._needs_doc(conversation_id)
            detail = await self.service.get_document_detail(intent.doctype, intent.record_name, cookies, user)
            rows = [{"field": key, "value": value} for key, value in {**detail.summary, "workflow_state": detail.workflow_state, "status": detail.status}.items()]
            actions = ", ".join(action.action for action in detail.available_actions) or "No actions available"
            summary = f"{detail.doctype} {detail.name} is in workflow state {detail.workflow_state or 'Unknown'}. Available actions: {actions}."
            return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary), ToolCallPart(tool_name="workflow_document_detail", status="success", input_summary=detail.name, output_summary=actions), build_table_part(f"{detail.doctype} {detail.name}", rows)], SourceMeta(source_type="tool", source_name="ERPNext Workflow", record_count=1, filters={"doctype": detail.doctype, "name": detail.name}))

        if intent.intent == "workflow_apply_action":
            if not intent.doctype or not intent.record_name or not (intent.data or {}).get("action"):
                return self._needs_doc(conversation_id)
            action = str((intent.data or {}).get("action"))
            detail = await self.service.get_document_detail(intent.doctype, intent.record_name, cookies, user)
            if action not in {item.action for item in detail.available_actions}:
                summary = "This workflow action is not available for your user on this document."
                return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary), ToolCallPart(tool_name="workflow_safety_guard", status="error", input_summary=action, output_summary="Action not available")], permission=PermissionMeta(allowed=False, risk_level="medium", reason=summary))
            confirmation_id = new_id("workflow_conf")
            summary = f'Please confirm ERPNext workflow action "{action}" on {intent.doctype} {intent.record_name}. This will follow ERPNext workflow rules.'
            return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary), ConfirmationPart(confirmation_id=confirmation_id, title=f"Confirm {action}", description=summary, confirm_label=action, risk_level="medium")], SourceMeta(source_type="tool", source_name="ERPNext Workflow", record_count=1, filters={"doctype": intent.doctype, "name": intent.record_name, "action": action}), PermissionMeta(allowed=True, risk_level="medium", confirmation_required=True))

        return self._needs_doc(conversation_id)

    @staticmethod
    def _response(conversation_id: str, intent: str, summary: str, parts: list, source: SourceMeta | None = None, permission: PermissionMeta | None = None) -> AssistantChatResponse:
        message_id = new_id("msg")
        return AssistantChatResponse(conversation_id=conversation_id, message_id=message_id, intent=intent, parts=parts, source=source, permission=permission or PermissionMeta(allowed=True), suggested_actions=[SuggestedAction(label="Refresh", action_type="refresh_workflow"), SuggestedAction(label="Open in ERPNext", action_type="open_erpnext")], id=message_id, content=summary, created_at=utc_now())

    @classmethod
    def _needs_doc(cls, conversation_id: str) -> AssistantChatResponse:
        summary = "Please specify the ERPNext document type and document number."
        return cls._response(conversation_id, "workflow_missing_document", summary, [TextPart(content=summary)], permission=PermissionMeta(allowed=False, risk_level="medium", reason=summary))
