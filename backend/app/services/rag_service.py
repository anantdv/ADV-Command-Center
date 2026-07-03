import json

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.llm.base import BaseLLMProvider, LLMMessage
from app.llm.privacy_gateway import PrivacyViolationError, assert_safe_rag_payload
from app.llm.prompts import build_rag_system_prompt
from app.llm.vertex_gemini_provider import VertexGeminiProvider
from app.schemas.knowledge import RAGAnswerRequest, RAGAnswerResponse, RAGCitation, KnowledgeSearchRequest
from app.services.knowledge_service import KnowledgeService, knowledge_service
from app.utils.citation_builder import build_citations


class RAGService:
    def __init__(self, knowledge: KnowledgeService | None = None, provider: BaseLLMProvider | None = None):
        self.knowledge = knowledge or knowledge_service
        self.provider = provider

    async def answer_question(self, request: RAGAnswerRequest, user: str, user_roles: list[str]) -> RAGAnswerResponse:
        try:
            results = await self.knowledge.search(KnowledgeSearchRequest(query=request.question,module=request.module,top_k=min(request.top_k,settings.rag_max_context_chunks)),user,user_roles)
        except PrivacyViolationError as exc:
            await self._audit("rag_privacy_blocked",user,request,[],True)
            return self._escalation("The question contains data that cannot be sent to the knowledge AI.")
        if not results:
            await self._audit("rag_no_answer",user,request,[],True)
            return self._escalation("No approved knowledge source matched this question.")

        citations = build_citations(results)
        context = [{"citation_id":citation.citation_id,"source_id":result.source_id,"source_type":result.source_type,"title":result.title,"content":result.snippet} for citation,result in zip(citations,results)]
        outbound = {"question":request.question,"approved_context":context,"citation_ids":[item.citation_id for item in citations],"source_titles":[item.title for item in citations]}
        try:
            assert_safe_rag_payload(outbound)
        except PrivacyViolationError:
            await self._audit("rag_privacy_blocked",user,request,citations,True)
            return self._escalation("The retrieved context did not pass the private knowledge boundary.")

        if settings.use_mock_data and self.provider is None:
            answer = f"According to {citations[0].citation_label}: {results[0].snippet}"
            response = RAGAnswerResponse(answer=answer,citations=[citations[0]],confidence=min(max(results[0].score,.5),.95))
        else:
            try:
                provider = self.provider or self._vertex_provider()
                model_response = await provider.complete(
                    [LLMMessage(role="system",content=build_rag_system_prompt()),LLMMessage(role="user",content=json.dumps(outbound,separators=(",",":")))],
                    {"type":"object","properties":{"answer":{"type":"string"},"citation_ids":{"type":"array","items":{"type":"string"}},"confidence":{"type":"number"},"insufficient":{"type":"boolean"}},"required":["answer","citation_ids","confidence","insufficient"]},
                    purpose="approved_knowledge_rag",
                )
                parsed = json.loads(model_response.content)
                citation_map = {item.citation_id:item for item in citations}
                selected = [citation_map[item] for item in parsed.get("citation_ids",[]) if item in citation_map]
                insufficient = bool(parsed.get("insufficient")) or (settings.rag_require_citations and not selected)
                if insufficient:
                    response = self._escalation("The approved sources did not contain a sufficiently cited answer.")
                else:
                    response = RAGAnswerResponse(answer=str(parsed["answer"]),citations=selected,confidence=min(max(float(parsed.get("confidence",0)),0),1))
            except Exception:
                response = self._escalation("The knowledge assistant could not safely produce a cited answer.")
        await self._audit("rag_no_answer" if response.escalation_recommended else "rag_answer_generated",user,request,response.citations,response.escalation_recommended)
        return response

    @staticmethod
    def _vertex_provider() -> VertexGeminiProvider:
        return VertexGeminiProvider(settings.google_cloud_project or "",settings.google_cloud_location,settings.rag_gemini_model,settings.llm_timeout_seconds,settings.llm_temperature,settings.llm_max_output_tokens)

    @staticmethod
    def _escalation(reason: str) -> RAGAnswerResponse:
        return RAGAnswerResponse(answer="I could not find a reliable answer in the approved knowledge base.",citations=[],confidence=0,escalation_recommended=True,escalation_reason=reason)

    @staticmethod
    async def _audit(action: str,user: str,request: RAGAnswerRequest,citations: list[RAGCitation],escalation: bool) -> None:
        await log_audit_event(AuditEvent(user=user,conversation_id=request.conversation_id,action=action,agent_name="rag_service",allowed=action!="rag_privacy_blocked",risk_level="low",module=request.module,query_hash=KnowledgeService.query_hash(request.question),citation_ids=[item.citation_id for item in citations],top_k=request.top_k,escalation_recommended=escalation,erp_data_sent=False))


rag_service = RAGService()
