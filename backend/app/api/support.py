from fastapi import APIRouter

from app.dependencies import CurrentUserDep
from app.schemas.common import ApiResponse
from app.schemas.support import AiHelpRequest, AiHelpResponse, Ticket, TicketCreate
from app.services.support_service import support_service

router = APIRouter(prefix="/support", tags=["Support"])


@router.get("/tickets", response_model=ApiResponse[list[Ticket]])
async def tickets(_: CurrentUserDep) -> ApiResponse[list[Ticket]]: return ApiResponse(data=await support_service.list_tickets())


@router.post("/tickets", response_model=ApiResponse[Ticket])
async def create_ticket(payload: TicketCreate, _: CurrentUserDep) -> ApiResponse[Ticket]: return ApiResponse(data=await support_service.create_ticket(payload), message="Ticket created")


@router.post("/ai-help", response_model=ApiResponse[AiHelpResponse])
async def ai_help(payload: AiHelpRequest, _: CurrentUserDep) -> ApiResponse[AiHelpResponse]: return ApiResponse(data=await support_service.ai_help(payload))
