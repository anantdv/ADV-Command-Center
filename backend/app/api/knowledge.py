from fastapi import APIRouter, Query

from app.dependencies import CurrentUserDep
from app.schemas.common import ApiResponse
from app.schemas.knowledge import IngestionResult, KnowledgeSearchRequest, KnowledgeSearchResult, KnowledgeSource, KnowledgeSourceCreateRequest, RAGAnswerRequest, RAGAnswerResponse
from app.services.knowledge_service import knowledge_service
from app.services.rag_service import rag_service

router = APIRouter(prefix="/knowledge", tags=["Knowledge"])


@router.get("/sources", response_model=ApiResponse[list[KnowledgeSource]])
async def list_sources(user: CurrentUserDep, status: str | None = Query(default=None)) -> ApiResponse[list[KnowledgeSource]]:
    return ApiResponse(data=await knowledge_service.list_sources(status,user.roles))


@router.post("/sources", response_model=ApiResponse[KnowledgeSource])
async def create_source(payload: KnowledgeSourceCreateRequest,user: CurrentUserDep) -> ApiResponse[KnowledgeSource]:
    return ApiResponse(data=await knowledge_service.create_source(payload,user.user),message="Knowledge source created as draft")


@router.get("/sources/{source_id}", response_model=ApiResponse[KnowledgeSource])
async def get_source(source_id: str,user: CurrentUserDep) -> ApiResponse[KnowledgeSource]:
    return ApiResponse(data=await knowledge_service.get_source(source_id,user.roles))


@router.post("/sources/{source_id}/approve", response_model=ApiResponse[KnowledgeSource])
async def approve_source(source_id: str,user: CurrentUserDep) -> ApiResponse[KnowledgeSource]:
    return ApiResponse(data=await knowledge_service.approve_source(source_id,user.user,user.roles),message="Knowledge source approved")


@router.post("/sources/{source_id}/ingest", response_model=ApiResponse[IngestionResult])
async def ingest_source(source_id: str,user: CurrentUserDep) -> ApiResponse[IngestionResult]:
    return ApiResponse(data=IngestionResult.model_validate(await knowledge_service.ingest_source(source_id,user.user,user.roles)),message="Approved source indexed")


@router.post("/search", response_model=ApiResponse[list[KnowledgeSearchResult]])
async def search(payload: KnowledgeSearchRequest,user: CurrentUserDep) -> ApiResponse[list[KnowledgeSearchResult]]:
    return ApiResponse(data=await knowledge_service.search(payload,user.user,user.roles))


@router.post("/ask", response_model=ApiResponse[RAGAnswerResponse])
async def ask(payload: RAGAnswerRequest,user: CurrentUserDep) -> ApiResponse[RAGAnswerResponse]:
    return ApiResponse(data=await rag_service.answer_question(payload,user.user,user.roles))
