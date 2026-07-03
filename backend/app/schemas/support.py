from typing import Literal

from pydantic import AliasChoices, Field

from app.schemas.common import CamelModel, PermissionMeta


class TicketCreate(CamelModel):
    subject: str
    description: str
    priority: Literal["High", "Medium", "Low"] = "Medium"


class Ticket(CamelModel):
    id: str
    subject: str
    priority: Literal["High", "Medium", "Low"]
    status: Literal["Open", "In Progress", "Resolved"]
    assigned_to: str
    created: str
    permissions: PermissionMeta


class AiHelpRequest(CamelModel):
    message: str = Field(validation_alias=AliasChoices("message", "question"))
    module: str | None = None
    conversation_id: str | None = None


class AiHelpResponse(CamelModel):
    answer: str
    suggested_actions: list[str] = Field(default_factory=list)
    create_ticket_recommended: bool = False
    citations: list[dict] = Field(default_factory=list)
    escalation_recommended: bool = False
    escalation_reason: str | None = None
    suggested_ticket_subject: str | None = None
    suggested_ticket_description: str | None = None


class EscalateSupportRequest(CamelModel):
    question: str
    ai_answer: str | None = None
    citations: list[dict] = Field(default_factory=list)
    subject: str
    description: str
    priority: Literal["Low", "Medium", "High", "Urgent"] = "Medium"
    module: str | None = None
    conversation_id: str | None = None


class SupportQuestionRequest(AiHelpRequest):
    """Explicit RAG support request contract."""


class SupportAnswerResponse(AiHelpResponse):
    """Explicit cited RAG support response contract."""
