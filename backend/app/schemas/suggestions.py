from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas.common import CamelModel


SuggestionType = Literal["prompt", "action", "ui_action", "navigation", "export", "pin", "workflow_action", "crud_confirmation"]
SuggestionRisk = Literal["low", "medium", "high"]
ResultType = Literal[
    "table",
    "chart",
    "analytics",
    "report_composer",
    "workflow_pending_list",
    "workflow_detail",
    "crud_preview",
    "crud_created",
    "document_detail",
    "file_generated",
    "empty",
    "error",
    "unknown",
]


class SuggestedPrompt(CamelModel):
    id: str
    label: str
    type: SuggestionType = "prompt"
    prompt: str | None = None
    action_type: str | None = None
    endpoint: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    icon: str | None = None
    risk: SuggestionRisk = "low"
    requires_confirmation: bool = False
    disabled: bool = False
    disabled_reason: str | None = None
    group: str | None = None


class SuggestionContext(CamelModel):
    conversation_id: str | None = None
    message_id: str | None = None
    previous_prompt: str | None = None
    result_type: ResultType = "unknown"
    doctype: str | None = None
    report_name: str | None = None
    analytics_key: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)
    row_count: int | None = None
    has_chart: bool = False
    chart_type: str | None = None
    document_name: str | None = None
    workflow_actions: list[str] = Field(default_factory=list)
    available_actions: list[str] = Field(default_factory=list)
    permissions: dict[str, Any] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)


class SuggestionResponse(CamelModel):
    suggestions: list[SuggestedPrompt]


class SuggestionExecuteRequest(CamelModel):
    suggestion: SuggestedPrompt
    conversation_id: str | None = None
