from __future__ import annotations

from app.agents.router_agent import IntentResult
from app.core.exceptions import AppError
from app.schemas.chat import AssistantChatResponse, PermissionMeta, SourceMeta, SuggestedAction, TextPart, ToolCallPart, WorkflowConfirmationPart
from app.schemas.suggestions import SuggestedPrompt
from app.schemas.workflow import ApplyWorkflowActionRequest, WorkflowActionPreviewRequest
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
                doctypes = (intent.data or {}).get("doctypes") if isinstance(intent.data, dict) else None
                if doctypes:
                    documents = []
                    filters = {"doctypes": doctypes}
                    for doctype in doctypes:
                        partial = await self.service.list_pending_approvals(doctype, cookies, intent.limit, user)
                        documents.extend(partial.documents)
                    from app.schemas.workflow import PendingApprovalsResponse
                    result = PendingApprovalsResponse(documents=documents[:intent.limit], total=len(documents[:intent.limit]), filters=filters)
                else:
                    result = await self.service.list_pending_approvals(intent.doctype, cookies, intent.limit, user)
            except AppError as exc:
                summary = f"I understood that you want pending approvals, but I could not fetch them from ERPNext. {exc.message}"
                return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary), ToolCallPart(tool_name="workflow_pending_approvals", status="error", output_summary=exc.message)], SourceMeta(source_type="tool", source_name="ERPNext Workflow", record_count=0, filters={"doctype": intent.doctype} if intent.doctype else {}), PermissionMeta(allowed=False, reason=exc.message))
            rows = [doc.model_dump(mode="json") | {"actions": ", ".join(action.action for action in doc.available_actions)} for doc in result.documents]
            summary = "You do not have any documents pending for approval." if not rows else f"I found {len(rows)} document{'s' if len(rows) != 1 else ''} pending for your approval."
            parts = [TextPart(content=summary), ToolCallPart(tool_name="workflow_pending_approvals", status="success", output_summary=f"{len(rows)} documents")]
            if rows:
                parts.append(build_table_part("Pending Approvals", rows, config={"result_type": "pending_approvals", "doctype_counts": [item.model_dump(mode="json") for item in result.doctype_counts]}))
            response = self._response(conversation_id, intent.intent, summary, parts, SourceMeta(source_type="tool", source_name="ERPNext Workflow", record_count=len(rows), filters=result.filters))
            response.suggestions = _pending_approval_suggestions(result.doctype_counts, result.filters)
            return response

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
                summary = "I need an open workflow document before I can apply that action."
                return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary)], permission=PermissionMeta(allowed=False, risk_level="medium", reason=summary))
            action = str((intent.data or {}).get("action"))
            try:
                preview = await self.preview_action(intent.doctype, intent.record_name, action, cookies, user)
            except AppError as exc:
                summary = exc.message or "This workflow action is no longer available for your user on this document."
                return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary), ToolCallPart(tool_name="workflow_action_preview", status="error", input_summary=action, output_summary=summary)], permission=PermissionMeta(allowed=False, risk_level="medium", reason=summary))
            summary = f'You are about to apply ERPNext workflow action "{preview.action}" to {preview.doctype} {preview.name}. Please confirm.'
            return self._response(
                conversation_id,
                intent.intent,
                summary,
                [
                    TextPart(content=summary),
                    ToolCallPart(tool_name="workflow_action_preview", status="success", input_summary=f"{preview.action} {preview.doctype} {preview.name}", output_summary=f"{preview.current_state or 'Current'} → {preview.next_state or 'Next'}"),
                    WorkflowConfirmationPart(doctype=preview.doctype, name=preview.name, action=preview.action, current_state=preview.current_state, next_state=preview.next_state, title=preview.title, summary=preview.summary, confirmation_id=preview.confirmation_id),
                ],
                SourceMeta(source_type="tool", source_name="ERPNext Workflow", record_count=1, filters={"doctype": preview.doctype, "name": preview.name, "action": preview.action}),
                PermissionMeta(allowed=True, risk_level="medium", confirmation_required=True),
            )

        return self._needs_doc(conversation_id)

    async def preview_action(self, doctype: str, name: str, action: str, cookies: dict | None = None, user: str = "unknown"):
        return await self.service.preview_action(WorkflowActionPreviewRequest(doctype=doctype, name=name, action=action), cookies, user)

    async def apply_action(self, request: ApplyWorkflowActionRequest, cookies: dict | None = None, user: str = "unknown"):
        return await self.service.apply_action(request, cookies, user)

    @staticmethod
    def _response(conversation_id: str, intent: str, summary: str, parts: list, source: SourceMeta | None = None, permission: PermissionMeta | None = None) -> AssistantChatResponse:
        message_id = new_id("msg")
        count = source.record_count if source else None
        actions = [SuggestedAction(label="Refresh", action_type="refresh_workflow")]
        if intent == "workflow_list_pending" and not count:
            actions.extend([
                SuggestedAction(label="Show Purchase Orders", action_type="prompt", payload={"prompt": "show purchase orders"}),
                SuggestedAction(label="Show Purchase Invoices", action_type="prompt", payload={"prompt": "show purchase invoices"}),
            ])
        return AssistantChatResponse(conversation_id=conversation_id, message_id=message_id, intent=intent, parts=parts, source=source, permission=permission or PermissionMeta(allowed=True), suggested_actions=actions, id=message_id, content=summary, created_at=utc_now())

    @classmethod
    def _needs_doc(cls, conversation_id: str) -> AssistantChatResponse:
        summary = "Please specify the ERPNext document type and document number."
        return cls._response(conversation_id, "workflow_missing_document", summary, [TextPart(content=summary)], permission=PermissionMeta(allowed=False, risk_level="medium", reason=summary))


def _pending_approval_suggestions(counts, filters: dict | None = None) -> list[SuggestedPrompt]:
    active_doctype = (filters or {}).get("doctype")
    suggestions = [
        SuggestedPrompt(id="sug_workflow_refresh", label="Refresh", type="action", action_type="refresh_pending_approvals", payload={"action": "refresh_pending_approvals"}, group="workflow"),
    ]
    if active_doctype:
        suggestions.append(SuggestedPrompt(id="sug_workflow_all", label="All Pending Approvals", type="action", action_type="filter_pending_approvals", payload={"action": "filter_pending_approvals", "doctype": None}, group="workflow"))
    for item in counts:
        doctype = item.doctype
        count = item.count
        suggestions.append(SuggestedPrompt(
            id=f"sug_workflow_filter_{_slug(doctype)}",
            label=f"{_plural_label(doctype)} · {count}",
            type="action",
            action_type="filter_pending_approvals",
            prompt=f"Show my pending {doctype} approvals",
            payload={"action": "filter_pending_approvals", "doctype": doctype, "count": count},
            group="workflow",
        ))
    return suggestions


def _plural_label(doctype: str) -> str:
    irregular = {
        "Purchase Order": "Purchase Orders",
        "Sales Order": "Sales Orders",
        "Sales Invoice": "Sales Invoices",
        "Purchase Invoice": "Purchase Invoices",
        "Quotation": "Quotations",
        "Pay Deduction Acceptance": "Pay Deduction Acceptances",
        "HP APPROVAL FORM": "HP Approval Forms",
    }
    if doctype in irregular:
        return irregular[doctype]
    words = doctype.replace("_", " ").split()
    if not words:
        return doctype
    words = [word if word.isupper() and len(word) <= 3 else word.title() for word in words]
    last = words[-1]
    if last.endswith("y") and len(last) > 1 and last[-2].lower() not in "aeiou":
        words[-1] = f"{last[:-1]}ies"
    elif last.endswith(("s", "x", "ch", "sh")):
        words[-1] = f"{last}es"
    else:
        words[-1] = f"{last}s"
    return " ".join(words)


def _slug(value: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in value.lower()).strip("_")
