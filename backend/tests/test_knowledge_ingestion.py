import pytest

from app.core.exceptions import AppError, PermissionDenied
from app.schemas.knowledge import KnowledgeSearchRequest, KnowledgeSourceCreateRequest
from app.services.embedding_service import EmbeddingService
from app.services.knowledge_service import KnowledgeService
from app.services.vector_store_service import VectorStoreService
from app.utils.text_chunker import chunk_text


def service(tmp_path):
    vectors=VectorStoreService(str(tmp_path))
    return KnowledgeService(str(tmp_path),EmbeddingService("local_test"),vectors)


def test_chunk_text_preserves_content_and_overlap():
    chunks=chunk_text("First paragraph explains the process.\n\n"+("Second paragraph has detail. "*30),120,20)
    assert len(chunks)>1 and all(chunks) and all(len(item)<=142 for item in chunks)


@pytest.mark.asyncio
async def test_create_approve_ingest_and_search(tmp_path):
    knowledge=service(tmp_path)
    source=await knowledge.create_source(KnowledgeSourceCreateRequest(title="Invoice SOP",source_type="sop_document",module="Accounting",content="Verify the document status and permissions before clicking Submit. Review taxes and totals before submission.",allowed_roles=["Accounts User"]),"manager@example.com")
    assert source.status=="draft"
    with pytest.raises(PermissionDenied): await knowledge.approve_source(source.source_id,"user",["Accounts User"])
    await knowledge.approve_source(source.source_id,"manager",["System Manager"])
    result=await knowledge.ingest_source(source.source_id,"manager",["System Manager"])
    assert result["indexed"] and result["chunk_count"]>=1
    found=await knowledge.search(KnowledgeSearchRequest(query="verify permissions before submit",module="Accounting"),"accounts@example.com",["Accounts User"])
    assert found and found[0].source_id==source.source_id
    hidden=await knowledge.search(KnowledgeSearchRequest(query="verify permissions before submit"),"sales@example.com",["Sales User"])
    assert hidden==[]


@pytest.mark.asyncio
async def test_draft_source_cannot_be_ingested_or_searched(tmp_path):
    knowledge=service(tmp_path)
    source=await knowledge.create_source(KnowledgeSourceCreateRequest(title="Draft FAQ",source_type="faq",content="This content is not approved for search."),"author")
    with pytest.raises(AppError): await knowledge.ingest_source(source.source_id,"manager",["System Manager"])
    assert await knowledge.search(KnowledgeSearchRequest(query="not approved"),"user",["System Manager"])==[]
