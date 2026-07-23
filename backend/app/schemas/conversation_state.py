from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ConversationState(str, Enum):
    IDLE = "IDLE"
    REPORT_RUNNING = "REPORT_RUNNING"
    REPORT_READY = "REPORT_READY"
    REPORT_DETAIL = "REPORT_DETAIL"
    ENTITY_SELECTION = "ENTITY_SELECTION"
    DRAFT_STARTED = "DRAFT_STARTED"
    DRAFT_COLLECTING = "DRAFT_COLLECTING"
    DRAFT_ENTITY_RESOLUTION = "DRAFT_ENTITY_RESOLUTION"
    DRAFT_INFORMATION_REQUIRED = "DRAFT_INFORMATION_REQUIRED"
    DRAFT_EDITING = "DRAFT_EDITING"
    DRAFT_PREVIEW = "DRAFT_PREVIEW"
    DRAFT_CONFIRMATION = "DRAFT_CONFIRMATION"
    DRAFT_CREATING = "DRAFT_CREATING"
    DRAFT_COMPLETED = "DRAFT_COMPLETED"
    DRAFT_CANCELLED = "DRAFT_CANCELLED"
    WAITING_USER_SELECTION = "WAITING_USER_SELECTION"
    WAITING_USER_CONFIRMATION = "WAITING_USER_CONFIRMATION"
    WAITING_USER_INPUT = "WAITING_USER_INPUT"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class ConversationContext(BaseModel):
    conversation_id: str
    active_state: ConversationState = ConversationState.IDLE
    draft_session_id: str | None = None
    report_session_id: str | None = None
    active_doctype: str | None = None
    active_document: str | None = None
    active_module: str | None = None
    pending_action: str | None = None
    pending_entities: list[dict[str, Any]] = Field(default_factory=list)
    pending_fields: list[dict[str, Any]] = Field(default_factory=list)
    selected_entities: dict[str, Any] = Field(default_factory=dict)
    confirmation_token: str | None = None
    preview_version: int = 0
    last_user_message: str | None = None
    last_ai_response: str | None = None
    last_action_timestamp: str | None = None


class StateDecision(BaseModel):
    route: Literal[
        "structured_selection",
        "structured_draft_field",
        "draft_continue",
        "report_followup",
        "new_draft",
        "general_router",
    ]
    normalized_message: str
    active_state: ConversationState
    reason: str
    composite: bool = False

