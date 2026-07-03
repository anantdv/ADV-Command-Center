from typing import Annotated

from fastapi import APIRouter, Depends

from app.agents.support_agent import SupportAgent
from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.support import AiHelpRequest, AiHelpResponse, EscalateSupportRequest, Ticket, TicketCreate
from app.services.support_service import support_service

router=APIRouter(prefix="/support",tags=["Support"])
CookiesDep=Annotated[dict[str,str],Depends(get_frappe_cookies)]


@router.get("/tickets",response_model=ApiResponse[list[Ticket]])
async def tickets(_:CurrentUserDep)->ApiResponse[list[Ticket]]: return ApiResponse(data=await support_service.list_tickets())


@router.post("/tickets",response_model=ApiResponse[Ticket])
async def create_ticket(payload:TicketCreate,_:CurrentUserDep)->ApiResponse[Ticket]: return ApiResponse(data=await support_service.create_ticket(payload),message="Ticket created")


@router.post("/ai-help",response_model=ApiResponse[AiHelpResponse])
async def ai_help(payload:AiHelpRequest,user:CurrentUserDep)->ApiResponse[AiHelpResponse]: return ApiResponse(data=await support_service.ai_help(payload,user.user,user.roles))


@router.post("/escalate",response_model=ApiResponse[Ticket])
async def escalate(payload:EscalateSupportRequest,user:CurrentUserDep,cookies:CookiesDep)->ApiResponse[Ticket]: return ApiResponse(data=await SupportAgent().escalate(payload,user.user,cookies),message="Support ticket created")
