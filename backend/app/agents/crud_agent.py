from app.agents.router_agent import IntentResult
from app.schemas.chat import AssistantChatResponse, ConfirmationPart, MissingFieldsPart, PermissionMeta, RecordPreviewPart, TextPart, ToolCallPart
from app.tools.crud_tools import CrudTools
from app.utils.datetime import utc_now
from app.utils.ids import new_id


class CrudAgent:
    def __init__(self, tools: CrudTools | None = None): self.tools=tools or CrudTools()

    async def handle(self, intent: IntentResult, cookies: dict | None = None, user: str = "unknown") -> AssistantChatResponse:
        if not intent.doctype or intent.intent not in {"crud_create","crud_update"}: raise ValueError("CrudAgent requires a supported CRUD intent")
        conversation_id=intent.conversation_id or new_id("conv");message_id=new_id("msg")
        if intent.intent == "crud_create":
            preview=await self.tools.prepare_create_record(doctype=intent.doctype,data=intent.data or {},conversation_id=conversation_id,message_id=message_id,cookies=cookies,user=user)
        else:
            if not intent.record_name or not intent.data:
                summary="Please include the record name, the field to change, and its new value."
                return self._response(conversation_id,message_id,intent.intent,summary,[TextPart(content=summary)])
            preview=await self.tools.prepare_update_record(doctype=intent.doctype,record_name=intent.record_name,data=intent.data,conversation_id=conversation_id,message_id=message_id,cookies=cookies,user=user)
        if preview.missing_fields:
            summary=f"I can prepare this {intent.doctype}, but I need a few required fields first."
            return self._response(conversation_id,message_id,intent.intent,summary,[TextPart(content=summary),MissingFieldsPart(doctype=intent.doctype,operation=preview.operation,fields=preview.missing_fields,collected_data=preview.data,record_name=preview.record_name,conversation_id=conversation_id,message_id=message_id)])
        verb="creation" if preview.operation=="create" else "update"
        summary=f"I prepared a draft {intent.doctype} {verb} request. Please review and confirm before I apply it in ERPNext."
        parts=[TextPart(content=summary),ToolCallPart(tool_name=f"prepare_{preview.operation}_record",status="success",input_summary=f"{preview.operation} {intent.doctype}",output_summary="Confirmation preview prepared"),RecordPreviewPart(operation=preview.operation,doctype=intent.doctype,record_name=preview.record_name,before_data=preview.before_data,after_data=preview.after_data or preview.data),ConfirmationPart(confirmation_id=preview.confirmation_id or "",title=f"Confirm {intent.doctype} {verb}",description=f"Review the fields above. This will {preview.operation} the {intent.doctype} using your current ERPNext session.",confirm_label="Create Draft" if preview.operation=="create" else "Apply Update")]
        permission=PermissionMeta.model_validate(preview.permission or {"allowed":True,"risk_level":"medium","confirmation_required":True})
        permission.confirmation_required=True;permission.risk_level="medium"
        return self._response(conversation_id,message_id,intent.intent,summary,parts,permission)

    @staticmethod
    def _response(conversation_id: str, message_id: str, intent: str, summary: str, parts: list, permission: PermissionMeta | None = None) -> AssistantChatResponse:
        return AssistantChatResponse(conversation_id=conversation_id,message_id=message_id,intent=intent,parts=parts,permission=permission,id=message_id,content=summary,created_at=utc_now())


CRUDAgent = CrudAgent
