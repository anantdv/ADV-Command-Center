from fastapi import APIRouter, Request

from app.db.seed import INVOICES
from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.chat import AssistantChatResponse, ChatActionResult, ChatMessage, ChatMessageRequest, Conversation, ConversationCreate
from app.schemas.common import ApiResponse
from app.schemas.dashboard import PinChatResultRequest, PinChatResultResponse
from app.schemas.crud import CancelCrudResponse, ConfirmCrudRequest, ConfirmCrudResponse, ContinueCrudRequest
from app.services.chat_service import chat_service

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=ApiResponse[list[Conversation]])
async def conversations(_: CurrentUserDep) -> ApiResponse[list[Conversation]]: return ApiResponse(data=await chat_service.list_conversations())


@router.post("/conversations", response_model=ApiResponse[Conversation])
async def create_conversation(payload: ConversationCreate, _: CurrentUserDep) -> ApiResponse[Conversation]: return ApiResponse(data=await chat_service.create_conversation(payload))


@router.get("/conversations/{conversation_id}/messages", response_model=ApiResponse[list[ChatMessage]])
async def messages(conversation_id: str, _: CurrentUserDep) -> ApiResponse[list[ChatMessage]]: return ApiResponse(data=await chat_service.get_messages(conversation_id))


@router.post("/message", response_model=ApiResponse[AssistantChatResponse])
async def send_message(payload: ChatMessageRequest, request: Request, user: CurrentUserDep) -> ApiResponse[AssistantChatResponse]:
    return ApiResponse(
        data=await chat_service.send_chat_message(
            payload,
            get_frappe_cookies(request),
            user.user,
            user.roles,
        )
    )


@router.post("/actions/confirm", response_model=ApiResponse[ConfirmCrudResponse])
async def confirm_crud(payload: ConfirmCrudRequest, request: Request, user: CurrentUserDep) -> ApiResponse[ConfirmCrudResponse]:
    return ApiResponse(data=await chat_service.confirm_crud(payload, get_frappe_cookies(request), user.user))


@router.post("/actions/cancel", response_model=ApiResponse[CancelCrudResponse])
async def cancel_crud(payload: ConfirmCrudRequest, user: CurrentUserDep) -> ApiResponse[CancelCrudResponse]:
    return ApiResponse(data=await chat_service.cancel_crud(payload, user.user), message="Action cancelled.")


@router.post("/actions/continue-crud", response_model=ApiResponse[AssistantChatResponse])
async def continue_crud(payload: ContinueCrudRequest, request: Request, user: CurrentUserDep) -> ApiResponse[AssistantChatResponse]:
    return ApiResponse(data=await chat_service.continue_crud(payload, get_frappe_cookies(request), user.user))


@router.post("/actions/{action_id}/confirm", response_model=ApiResponse[ChatActionResult])
async def confirm(action_id: str, _: CurrentUserDep) -> ApiResponse[ChatActionResult]: return ApiResponse(data=await chat_service.action(action_id, True))


@router.post("/actions/{action_id}/cancel", response_model=ApiResponse[ChatActionResult])
async def cancel(action_id: str, _: CurrentUserDep) -> ApiResponse[ChatActionResult]: return ApiResponse(data=await chat_service.action(action_id, False))


@router.post("/actions/pin-to-dashboard", response_model=ApiResponse[PinChatResultResponse])
async def pin_to_dashboard(payload: PinChatResultRequest, request: Request, user: CurrentUserDep) -> ApiResponse[PinChatResultResponse]:
    return ApiResponse(data=await chat_service.pin_to_dashboard(payload, get_frappe_cookies(request), user.user))


@router.get("/seed", response_model=ApiResponse[dict])
async def seed(_: CurrentUserDep) -> ApiResponse[dict]: return ApiResponse(data={"invoices": INVOICES})
