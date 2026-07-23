from __future__ import annotations

from typing import Any

from app.schemas.conversation_state import ConversationContext
from app.schemas.workflow import WorkflowAction, WorkflowDocumentContext


class WorkflowContextResolver:
    def build_context_from_record_detail(
        self,
        record_detail: dict[str, Any],
        message_id: str | None = None,
        result_id: str | None = None,
    ) -> WorkflowDocumentContext | None:
        actions = record_detail.get("available_workflow_actions") or record_detail.get("availableActions") or []
        doctype = record_detail.get("doctype")
        name = record_detail.get("name")
        if not doctype or not name or not actions:
            return None
        return WorkflowDocumentContext(
            doctype=str(doctype),
            name=str(name),
            workflow_state=record_detail.get("workflow_state") or record_detail.get("workflowState"),
            available_actions=[WorkflowAction.model_validate(action) if isinstance(action, dict) else WorkflowAction(action=str(action)) for action in actions],
            source_message_id=message_id,
            source_result_id=result_id,
        )

    def resolve_from_conversation(self, message: str, conversation_context: ConversationContext | dict[str, Any] | None) -> WorkflowDocumentContext | None:
        if not conversation_context:
            return None
        context = conversation_context if isinstance(conversation_context, ConversationContext) else ConversationContext.model_validate(conversation_context)
        if not context.active_doctype or not context.active_document or not context.active_workflow_actions:
            return None
        return WorkflowDocumentContext(
            doctype=context.active_doctype,
            name=context.active_document,
            workflow_state=context.active_workflow_state,
            available_actions=[WorkflowAction.model_validate(action) for action in context.active_workflow_actions],
        )


workflow_context_resolver = WorkflowContextResolver()
