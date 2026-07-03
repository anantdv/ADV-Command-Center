from fastapi import APIRouter,Query,Request

from app.dependencies import CurrentUserDep,get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.communications import *
from app.services.communication_service import communication_service

router=APIRouter(prefix="/communications",tags=["Communications"])

@router.get("",response_model=ApiResponse[CommunicationList])
async def list_communications(request:Request,user:CurrentUserDep,folder:str="inbox",search:str|None=None,limit:int=Query(20,ge=1,le=100),start:int=Query(0,ge=0),unread:bool=False,linked:bool|None=None,has_attachments:bool=False,reference_doctype:str|None=None):
    return ApiResponse(data=await communication_service.list(folder,search,limit,start,get_frappe_cookies(request),unread=unread,linked=linked,has_attachments=has_attachments,reference_doctype=reference_doctype))

@router.get("/templates",response_model=ApiResponse[list[EmailTemplateItem]])
async def templates(request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.templates(get_frappe_cookies(request)))
@router.post("/templates/{name}/render",response_model=ApiResponse[EmailTemplateItem])
async def render(name:str,payload:RenderTemplateRequest,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.render_template(name,payload.context,get_frappe_cookies(request)))
@router.get("/{name}",response_model=ApiResponse[CommunicationThread])
async def thread(name:str,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.thread(name,get_frappe_cookies(request)))
@router.post("/send",response_model=ApiResponse[ActionResult])
async def send(payload:SendEmailRequest,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.send(payload,get_frappe_cookies(request),user.user),message="Email queued")
@router.post("/{name}/reply",response_model=ApiResponse[ActionResult])
async def reply(name:str,payload:ReplyRequest,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.reply(name,payload,get_frappe_cookies(request),user.user))
@router.post("/{name}/forward",response_model=ApiResponse[ActionResult])
async def forward(name:str,payload:ForwardRequest,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.forward(name,payload,get_frappe_cookies(request),user.user))
@router.post("/{name}/link",response_model=ApiResponse[ActionResult])
async def link(name:str,payload:LinkRequest,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.link(name,payload,get_frappe_cookies(request),user.user))
@router.post("/ai/draft",response_model=ApiResponse[AiMailDraft])
async def ai_draft(payload:AiMailDraftRequest,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.ai_draft(payload,get_frappe_cookies(request),user.user))
@router.post("/{name}/convert",response_model=ApiResponse[ActionResult])
async def convert(name:str,payload:ConversionRequest,request:Request,user:CurrentUserDep):return ApiResponse(data=await communication_service.convert(name,payload.action,get_frappe_cookies(request),user.user))
