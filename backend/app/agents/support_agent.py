from app.core.audit import AuditEvent, log_audit_event
from app.schemas.knowledge import RAGAnswerRequest
from app.schemas.support import AiHelpResponse, EscalateSupportRequest
from app.services.rag_service import RAGService, rag_service


class SupportAgent:
    def __init__(self,rag:RAGService|None=None): self.rag=rag or rag_service

    async def answer(self,question:str,module:str|None,conversation_id:str|None,user:str,roles:list[str])->AiHelpResponse:
        result=await self.rag.answer_question(RAGAnswerRequest(question=question,module=module,conversation_id=conversation_id),user,roles)
        response=AiHelpResponse(answer=result.answer,citations=[item.model_dump(mode="json",by_alias=True) for item in result.citations],escalation_recommended=result.escalation_recommended,escalation_reason=result.escalation_reason,create_ticket_recommended=result.escalation_recommended,suggested_actions=["Open cited source"] if result.citations else ["Create support ticket"],suggested_ticket_subject=f"ERPNext help: {question[:80]}" if result.escalation_recommended else None,suggested_ticket_description=f"Question: {question}\n\nKnowledge AI result: {result.answer}" if result.escalation_recommended else None)
        await log_audit_event(AuditEvent(user=user,conversation_id=conversation_id,action="support_ai_answered",agent_name="support_agent",allowed=True,risk_level="low",module=module,citation_ids=[item.citation_id for item in result.citations],escalation_recommended=result.escalation_recommended,erp_data_sent=False))
        return response

    async def escalate(self,request:EscalateSupportRequest,user:str,cookies:dict|None=None):
        from app.services.support_service import support_service
        ticket=await support_service.create_escalated_ticket(request,cookies)
        await log_audit_event(AuditEvent(user=user,conversation_id=request.conversation_id,action="support_escalated",agent_name="support_agent",allowed=True,risk_level="medium",module=request.module,citation_ids=[str(item.get("citationId") or item.get("citation_id")) for item in request.citations],record_name=ticket.id,erp_data_sent=False))
        return ticket
