from __future__ import annotations

from fastapi import APIRouter, Request

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError
from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.chat import AssistantChatResponse, ChatMessageRequest
from app.schemas.common import ApiResponse
from app.schemas.crud import ConfirmCrudRequest
from app.schemas.suggestions import SuggestionContext, SuggestionExecuteRequest, SuggestionResponse
from app.schemas.workflow import WorkflowActionPreviewRequest
from app.services.chat_service import chat_service
from app.services.suggestion_service import suggestion_service
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/suggestions", tags=["Suggestions"])


@router.post("/generate", response_model=ApiResponse[SuggestionResponse])
async def generate(payload: SuggestionContext, request: Request, user: CurrentUserDep) -> ApiResponse[SuggestionResponse]:
    return ApiResponse(data=await suggestion_service.generate_suggestions(payload, user.roles, get_frappe_cookies(request), user.user))


@router.post("/execute", response_model=ApiResponse[AssistantChatResponse | dict])
async def execute(payload: SuggestionExecuteRequest, request: Request, user: CurrentUserDep) -> ApiResponse[AssistantChatResponse | dict]:
    if not settings.enable_suggestion_execute_endpoint:
        raise AppError("Suggestion execution is disabled.", 403)
    suggestion = payload.suggestion
    if suggestion.disabled:
        raise AppError(suggestion.disabled_reason or "This suggestion is not available yet.", 422)
    await log_audit_event(AuditEvent(user=user.user, conversation_id=payload.conversation_id, action="suggestion_clicked", agent_name="suggestion_service", tool_name=suggestion.action_type, allowed=True, risk_level=suggestion.risk, input_summary=suggestion.label, erp_data_sent=False))
    if suggestion.type == "prompt" and suggestion.prompt:
        response = await chat_service.send_chat_message(ChatMessageRequest(conversation_id=payload.conversation_id, message=suggestion.prompt), get_frappe_cookies(request), user.user, user.roles)
        return ApiResponse(data=response)
    if suggestion.type == "export":
        fmt = suggestion.payload.get("format") or "xlsx"
        prompt = f"export this custom report to {fmt}"
        response = await chat_service.send_chat_message(ChatMessageRequest(conversation_id=payload.conversation_id, message=prompt), get_frappe_cookies(request), user.user, user.roles)
        return ApiResponse(data=response)
    if suggestion.type == "pin":
        response = await chat_service.send_chat_message(ChatMessageRequest(conversation_id=payload.conversation_id, message="pin this report to overview"), get_frappe_cookies(request), user.user, user.roles)
        return ApiResponse(data=response)
    if suggestion.type == "workflow_action":
        doctype = suggestion.payload.get("doctype")
        name = suggestion.payload.get("name")
        action = suggestion.payload.get("action")
        if not doctype or not name or not action:
            raise AppError("This workflow action is missing document context.", 422)
        response = await WorkflowService().preview_action(WorkflowActionPreviewRequest(doctype=str(doctype), name=str(name), action=str(action)), get_frappe_cookies(request), user.user)
        return ApiResponse(data=response.model_dump(mode="json"))
    if suggestion.type == "crud_confirmation":
        confirmation_id = str(suggestion.payload.get("confirmation_id") or "")
        if not confirmation_id:
            raise AppError("This confirmation suggestion is no longer valid.", 422)
        if suggestion.action_type == "cancel_draft":
            result = await chat_service.cancel_crud(ConfirmCrudRequest(confirmation_id=confirmation_id), user.user)
            return ApiResponse(data=result.model_dump(mode="json"))
        result = await chat_service.confirm_crud(ConfirmCrudRequest(confirmation_id=confirmation_id), get_frappe_cookies(request), user.user)
        return ApiResponse(data=result.model_dump(mode="json"))
    if suggestion.type == "navigation":
        return ApiResponse(data={"action_type": suggestion.action_type, "payload": suggestion.payload})
    raise AppError("I could not complete that suggested action. Please try again or run it manually.", 422)
