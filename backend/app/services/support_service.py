from datetime import date

from app.config import settings
from app.db.seed import FULL_PERMISSION
from app.frappe.client import FrappeClient
from app.frappe.paths import CREATE_SUPPORT_TICKET
from app.schemas.common import PermissionMeta
from app.schemas.support import AiHelpRequest, AiHelpResponse, EscalateSupportRequest, Ticket, TicketCreate
from app.utils.ids import new_id


class SupportService:
    def __init__(self)->None:
        permission=PermissionMeta(**FULL_PERMISSION)
        self.tickets=[Ticket(id="SUP-2026-0148",subject="Unable to submit Sales Invoice",priority="High",status="In Progress",assigned_to="Rahul Mehta",created="01 Jul 2026",permissions=permission),Ticket(id="SUP-2026-0142",subject="Payment Entry not reflecting",priority="Medium",status="Open",assigned_to="AI Triage",created="30 Jun 2026",permissions=permission),Ticket(id="SUP-2026-0133",subject="Stock Ledger mismatch",priority="High",status="Resolved",assigned_to="Sneha Rao",created="28 Jun 2026",permissions=permission)]
    async def list_tickets(self)->list[Ticket]: return self.tickets
    async def create_ticket(self,request:TicketCreate)->Ticket:
        ticket=Ticket(id=new_id("SUP"),subject=request.subject,priority=request.priority,status="Open",assigned_to="AI Triage",created=date.today().isoformat(),permissions=PermissionMeta(**FULL_PERMISSION));self.tickets.insert(0,ticket);return ticket
    async def ai_help(self,request:AiHelpRequest,user:str="unknown",roles:list[str]|None=None)->AiHelpResponse:
        from app.agents.support_agent import SupportAgent
        return await SupportAgent().answer(request.message,request.module,request.conversation_id,user,roles or [])
    async def create_escalated_ticket(self,request:EscalateSupportRequest,cookies:dict|None=None)->Ticket:
        description=request.description+"\n\nQuestion: "+request.question
        if request.ai_answer: description+="\n\nAI answer: "+request.ai_answer
        if request.citations: description+="\n\nCitations: "+", ".join(str(item.get("citationLabel") or item.get("citation_label") or item.get("title")) for item in request.citations)
        priority="High" if request.priority=="Urgent" else request.priority
        if settings.use_mock_data:
            return await self.create_ticket(TicketCreate(subject=request.subject,description=description,priority=priority))
        client=FrappeClient(settings.frappe_base_url,settings.frappe_auth_mode,settings.frappe_api_key,settings.frappe_api_secret,settings.frappe_session_cookie_name)
        payload=await client.post(CREATE_SUPPORT_TICKET,json={"subject":request.subject,"description":description,"priority":priority,"category":request.module,"conversation_id":request.conversation_id},cookies=cookies)
        data=payload.get("message",payload)
        if isinstance(data,dict) and "success" in data: data=data.get("data") or {}
        ticket=Ticket(id=str(data.get("name") or data.get("id") or new_id("SUP")),subject=request.subject,priority=priority,status="Open",assigned_to=str(data.get("assigned_to") or "Support Team"),created=date.today().isoformat(),permissions=PermissionMeta(**FULL_PERMISSION));self.tickets.insert(0,ticket);return ticket


support_service=SupportService()
