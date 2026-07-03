from typing import Any, Literal

from pydantic import Field

from app.schemas.common import CamelModel

KnowledgeSourceType = Literal[
    "training_course", "training_lesson", "training_assessment",
    "support_article", "sop_document", "faq", "uploaded_document",
    "media_transcript",
]


class KnowledgeSourceCreateRequest(CamelModel):
    title: str = Field(min_length=2, max_length=200)
    source_type: KnowledgeSourceType
    module: str | None = None
    description: str | None = None
    content: str | None = Field(default=None, max_length=2_000_000)
    file_id: str | None = None
    allowed_roles: list[str] = Field(default_factory=list)
    allowed_modules: list[str] = Field(default_factory=list)
    status: Literal["draft", "approved", "archived"] = "draft"


class KnowledgeSource(CamelModel):
    source_id: str
    title: str
    source_type: KnowledgeSourceType
    module: str | None = None
    description: str | None = None
    status: Literal["draft", "approved", "archived"]
    allowed_roles: list[str] = Field(default_factory=list)
    allowed_modules: list[str] = Field(default_factory=list)
    file_id: str | None = None
    created_by: str | None = None
    created_at: str
    updated_at: str | None = None


class KnowledgeChunk(CamelModel):
    chunk_id: str
    source_id: str
    chunk_index: int
    title: str
    content: str
    module: str | None = None
    source_type: KnowledgeSourceType
    citation_label: str
    allowed_roles: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchRequest(CamelModel):
    query: str = Field(min_length=2, max_length=8000)
    module: str | None = None
    top_k: int = Field(5, ge=1, le=20)


class KnowledgeSearchResult(CamelModel):
    chunk_id: str
    source_id: str
    title: str
    snippet: str
    score: float
    citation_label: str
    source_type: KnowledgeSourceType
    module: str | None = None


class RAGAnswerRequest(CamelModel):
    question: str = Field(min_length=2, max_length=8000)
    module: str | None = None
    conversation_id: str | None = None
    top_k: int = Field(5, ge=1, le=20)


class RAGCitation(CamelModel):
    citation_id: str
    source_id: str
    title: str
    citation_label: str
    snippet: str
    source_type: KnowledgeSourceType | None = None


class RAGAnswerResponse(CamelModel):
    answer: str
    citations: list[RAGCitation] = Field(default_factory=list)
    confidence: float | None = None
    escalation_recommended: bool = False
    escalation_reason: str | None = None


class IngestionResult(CamelModel):
    source_id: str
    chunk_count: int
    indexed: bool
