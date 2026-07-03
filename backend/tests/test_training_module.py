import pytest

from app.agents.training_agent import TrainingAgent
from app.schemas.knowledge import KnowledgeSourceCreateRequest
from app.schemas.training import AssessmentSubmission, GenerateAssessmentRequest
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService
from app.services.training_service import TrainingService
from app.services.vector_store_service import VectorStoreService


@pytest.mark.asyncio
async def test_generate_and_submit_assessment_from_approved_source(tmp_path):
    knowledge=KnowledgeService(str(tmp_path),EmbeddingService("local_test"),VectorStoreService(str(tmp_path)))
    source=await knowledge.create_source(KnowledgeSourceCreateRequest(title="Training SOP",source_type="training_lesson",content="Always verify the document status and required fields before requesting approval."),"manager")
    await knowledge.approve_source(source.source_id,"manager",["System Manager"])
    await knowledge.ingest_source(source.source_id,"manager",["System Manager"])
    service=TrainingService();service.agent=TrainingAgent(knowledge)
    public=await service.generate_assessment(GenerateAssessmentRequest(source_id=source.source_id,question_count=1),"learner",["System Manager"])
    assert public.questions[0].correct_answer is None
    stored=service.assessments[public.assessment_id]
    answer=stored.questions[0].correct_answer
    result=await service.submit(public.assessment_id,AssessmentSubmission(answers={stored.questions[0].question_id:answer}),"learner")
    assert result.score==100 and result.passed


@pytest.mark.asyncio
async def test_training_course_and_leaderboard_contract():
    service=TrainingService()
    assert len(await service.list_courses())>=5
    assert (await service.leaderboard())[0]["rank"]==1
