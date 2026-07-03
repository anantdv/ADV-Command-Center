import json
import re

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError
from app.llm.base import BaseLLMProvider, LLMMessage
from app.llm.privacy_gateway import assert_safe_rag_payload
from app.llm.prompts import build_assessment_system_prompt
from app.llm.vertex_gemini_provider import VertexGeminiProvider
from app.schemas.training import AssessmentQuestion, GenerateAssessmentRequest, GeneratedAssessment
from app.services.knowledge_service import KnowledgeService, knowledge_service
from app.utils.ids import new_id


class TrainingAgent:
    def __init__(self, knowledge: KnowledgeService | None = None, provider: BaseLLMProvider | None = None):
        self.knowledge=knowledge or knowledge_service;self.provider=provider

    async def generate_assessment(self, request: GenerateAssessmentRequest, user: str, roles: list[str]) -> GeneratedAssessment:
        chunks=self.knowledge.chunks_for_source(request.source_id,roles)
        if not chunks: raise AppError("The approved source must be ingested before generating an assessment.",409)
        selected=chunks[:settings.rag_max_context_chunks]
        context=[{"citation_id":f"C{i}","source_id":chunk.source_id,"source_type":chunk.source_type,"title":chunk.title,"content":chunk.content} for i,chunk in enumerate(selected,1)]
        outbound={"question":f"Generate {request.question_count} {request.difficulty} assessment questions.","approved_context":context,"citation_ids":[item["citation_id"] for item in context],"source_titles":[item["title"] for item in context]}
        assert_safe_rag_payload(outbound)
        if settings.use_mock_data and self.provider is None:
            questions=self._deterministic_questions(selected[0].content,request.question_count)
        else:
            provider=self.provider or VertexGeminiProvider(settings.google_cloud_project or "",settings.google_cloud_location,settings.rag_gemini_model,settings.llm_timeout_seconds,0,settings.llm_max_output_tokens)
            response=await provider.complete([LLMMessage(role="system",content=build_assessment_system_prompt()),LLMMessage(role="user",content=json.dumps(outbound,separators=(",",":")))],purpose="training_assessment")
            try:
                values=json.loads(response.content).get("questions",[])
                questions=[AssessmentQuestion(question_id=new_id("q"),question=item["question"],options=item["options"][:4],correct_answer=item["correct_answer"],explanation=item.get("explanation")) for item in values[:request.question_count]]
            except (ValueError,KeyError,TypeError) as exc: raise AppError("Assessment generation returned invalid JSON.",502) from exc
        if not questions: raise AppError("No assessment questions could be generated.",502)
        assessment=GeneratedAssessment(assessment_id=new_id("assessment"),source_id=request.source_id,questions=questions)
        await log_audit_event(AuditEvent(user=user,action="training_assessment_generated",agent_name="training_agent",allowed=True,risk_level="low",source_id=request.source_id,record_count=len(questions),erp_data_sent=False))
        return assessment

    @staticmethod
    def _deterministic_questions(content: str,count: int) -> list[AssessmentQuestion]:
        sentences=[item.strip() for item in re.split(r"(?<=[.!?])\s+",content) if len(item.strip())>25]
        return [AssessmentQuestion(question_id=new_id("q"),question=f"Which statement is supported by the approved training material?",options=[sentence,"This action bypasses permissions.","All records are submitted automatically.","No review is required."],correct_answer=sentence,explanation="The first option is quoted from the approved source.") for sentence in (sentences or [content[:200]])[:count]]
