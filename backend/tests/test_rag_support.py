import json

import pytest

from app.agents.support_agent import SupportAgent
from app.schemas.support import EscalateSupportRequest
from app.llm.base import BaseLLMProvider, LLMResponse
from app.schemas.knowledge import KnowledgeSourceCreateRequest, RAGAnswerRequest
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService
from app.services.rag_service import RAGService
from app.services.vector_store_service import VectorStoreService


class CitedProvider(BaseLLMProvider):
    async def complete(self,messages,response_schema=None,**kwargs):
        return LLMResponse(content=json.dumps({"answer":"Check the document status and your Submit permission. [C1]","citation_ids":["C1"],"confidence":.9,"insufficient":False}),provider="vertex_gemini")


async def indexed(tmp_path):
    service=KnowledgeService(str(tmp_path),EmbeddingService("local_test"),VectorStoreService(str(tmp_path)))
    source=await service.create_source(KnowledgeSourceCreateRequest(title="Submission FAQ",source_type="support_article",module="Accounting",content="If submission fails, check the document status and confirm that your role has Submit permission."),"manager")
    await service.approve_source(source.source_id,"manager",["System Manager"])
    await service.ingest_source(source.source_id,"manager",["System Manager"])
    return service


@pytest.mark.asyncio
async def test_rag_answer_has_approved_citation(tmp_path,monkeypatch):
    monkeypatch.setattr("app.services.rag_service.settings.use_mock_data",False)
    rag=RAGService(await indexed(tmp_path),CitedProvider())
    answer=await rag.answer_question(RAGAnswerRequest(question="Why can I not submit?",module="Accounting"),"user",["System Manager"])
    assert answer.citations and not answer.escalation_recommended


@pytest.mark.asyncio
async def test_rag_no_chunks_recommends_escalation(tmp_path):
    rag=RAGService(KnowledgeService(str(tmp_path),EmbeddingService("local_test"),VectorStoreService(str(tmp_path))),CitedProvider())
    answer=await rag.answer_question(RAGAnswerRequest(question="Unknown procedure"),"user",["System Manager"])
    assert answer.escalation_recommended and answer.citations==[]


@pytest.mark.asyncio
async def test_support_ai_returns_cited_answer(tmp_path,monkeypatch):
    monkeypatch.setattr("app.services.rag_service.settings.use_mock_data",False)
    agent=SupportAgent(RAGService(await indexed(tmp_path),CitedProvider()))
    answer=await agent.answer("Why can I not submit?","Accounting",None,"user",["System Manager"])
    assert answer.citations and not answer.create_ticket_recommended


@pytest.mark.asyncio
async def test_support_escalation_creates_ticket_payload():
    ticket=await SupportAgent().escalate(EscalateSupportRequest(question="Unresolved approved procedure",subject="Need human help",description="The approved guide did not resolve this issue",priority="Medium"),"user")
    assert ticket.subject=="Need human help" and ticket.status=="Open"
