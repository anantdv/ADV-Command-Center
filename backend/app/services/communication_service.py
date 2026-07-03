from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.dependencies import get_frappe_client
from app.frappe import communications as frappe_communications, paths
from app.schemas.communications import *


MOCK_ITEMS=[
    CommunicationItem(name="COMM-0001",subject="Quotation request for 10 devices",sender="customer@example.com",recipients="sales@example.com",sent_or_received="Received",reference_doctype="Lead",reference_name="CRM-LEAD-0001",creation="2026-07-03 10:30:00",has_attachment=True,preview="Please send a quotation for 10 devices...",unread=True),
    CommunicationItem(name="COMM-0002",subject="Re: Purchase order delivery",sender="purchase@example.com",recipients="supplier@example.com",sent_or_received="Sent",reference_doctype="Purchase Order",reference_name="PUR-ORD-2026-0001",creation="2026-07-03 09:15:00",preview="The delivery schedule has been confirmed."),
    CommunicationItem(name="COMM-0003",subject="Invoice submission error",sender="support@example.com",recipients="admin@example.com",sent_or_received="Received",reference_doctype="Issue",reference_name="ISS-2026-0012",creation="2026-07-02 16:45:00",preview="We cannot submit the sales invoice...",unread=True),
]


class CommunicationService:
    def __init__(self): self.client=get_frappe_client()

    @staticmethod
    def _unwrap(payload:dict)->Any:
        value=payload.get("message",payload)
        return value.get("data") if isinstance(value,dict) and "success" in value else value

    async def list(self,folder="inbox",search=None,limit=20,start=0,cookies=None,**filters)->CommunicationList:
        if settings.use_mock_data:
            items=[item for item in MOCK_ITEMS if folder=="all" or (folder=="sent" and item.sent_or_received=="Sent") or (folder not in {"sent"} and item.sent_or_received=="Received")]
            if search: items=[item for item in items if search.lower() in f"{item.subject} {item.preview} {item.sender}".lower()]
            return CommunicationList(items=items[start:start+limit],total=len(items))
        data=self._unwrap(await frappe_communications.call(self.client,paths.GET_COMMUNICATIONS,{"filters":{"folder":folder,"search":search,**filters},"limit":limit,"start":start},cookies))
        return CommunicationList(items=data.get("items",data.get("data",[])),total=data.get("total",0))

    async def thread(self,name:str,cookies=None)->CommunicationThread:
        if settings.use_mock_data:
            item=next((x for x in MOCK_ITEMS if x.name==name),MOCK_ITEMS[0])
            return CommunicationThread(thread_id=item.subject,reference_doctype=item.reference_doctype,reference_name=item.reference_name,messages=[CommunicationMessage(**item.model_dump(),content=f"<p>{item.preview}</p>",attachments=[Attachment(name="FILE-1",file_name="quotation-request.pdf")] if item.has_attachment else [])])
        return CommunicationThread.model_validate(self._unwrap(await frappe_communications.call(self.client,paths.GET_COMMUNICATION_THREAD,{"communication_name":name},cookies)))

    async def send(self,request:SendEmailRequest,cookies,user)->ActionResult:
        return await self._action(paths.SEND_EMAIL,request.model_dump(),cookies,user,"communication_email_sent")
    async def reply(self,name,request:ReplyRequest,cookies,user)->ActionResult:
        return await self._action(paths.REPLY_TO_COMMUNICATION,{"communication_name":name,**request.model_dump()},cookies,user,"communication_replied")
    async def forward(self,name,request:ForwardRequest,cookies,user)->ActionResult:
        return await self._action(paths.FORWARD_COMMUNICATION,{"communication_name":name,**request.model_dump()},cookies,user,"communication_forwarded")
    async def link(self,name,request:LinkRequest,cookies,user)->ActionResult:
        return await self._action(paths.LINK_COMMUNICATION,{"communication_name":name,**request.model_dump()},cookies,user,"communication_linked")

    async def templates(self,cookies)->list[EmailTemplateItem]:
        if settings.use_mock_data:return [EmailTemplateItem(name="Quotation Follow-up",subject="Following up on your quotation",response="<p>Thank you for your interest. We are following up on the quotation.</p>"),EmailTemplateItem(name="Support Acknowledgement",subject="We received your request",response="<p>Our team is reviewing your request.</p>")]
        data=self._unwrap(await frappe_communications.call(self.client,paths.GET_EMAIL_TEMPLATES,{},cookies));return [EmailTemplateItem.model_validate(x) for x in data]

    async def render_template(self,name,context,cookies)->EmailTemplateItem:
        if settings.use_mock_data:return next((x for x in await self.templates(cookies) if x.name==name),EmailTemplateItem(name=name))
        return EmailTemplateItem.model_validate(self._unwrap(await frappe_communications.call(self.client,paths.RENDER_EMAIL_TEMPLATE,{"template_name":name,"context":context},cookies)))

    async def ai_draft(self,request:AiMailDraftRequest,cookies,user)->AiMailDraft:
        if settings.use_mock_data:return AiMailDraft(action=request.instruction,content=f"Draft preview: {request.content or 'Thank you for your email. We are reviewing your request and will respond shortly.'}")
        data=self._unwrap(await frappe_communications.call(self.client,paths.CREATE_AI_MAIL_DRAFT,request.model_dump(),cookies));return AiMailDraft.model_validate(data)

    async def convert(self,name,action,cookies,user)->ActionResult:
        path={"task":paths.CONVERT_EMAIL_TO_TASK,"issue":paths.CONVERT_EMAIL_TO_ISSUE,"lead":paths.CONVERT_EMAIL_TO_LEAD}[action]
        return await self._action(path,{"communication_name":name},cookies,user,f"communication_converted_to_{action}")

    async def _action(self,path,payload,cookies,user,event)->ActionResult:
        if settings.use_mock_data: result=ActionResult(name=f"MOCK-{event.upper()}",doctype="Communication",message="Action completed in mock mode.")
        else: result=ActionResult.model_validate(self._unwrap(await frappe_communications.call(self.client,path,payload,cookies)))
        await log_audit_event(AuditEvent(user=user,action=event,allowed=True,risk_level="medium",tool_name="communication_center",record_name=result.name,input_summary=event,output_summary=result.message))
        return result

communication_service=CommunicationService()
