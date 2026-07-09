from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.common import CamelModel
from app.schemas.crud import MissingField
from app.schemas.suggestions import SuggestedPrompt


class ConversationCreate(CamelModel):
    title: str | None = None


class Conversation(CamelModel):
    id: str
    title: str
    created_at: datetime
    updated_at: datetime


class ChatMessageRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")

    conversation_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("conversation_id", "conversationId"),
    )
    message: str = Field(validation_alias=AliasChoices("message", "content"), min_length=1)
    module_context: str | None = Field(
        default=None,
        validation_alias=AliasChoices("module_context", "moduleContext"),
    )
    company: str | None = None


# Backward-compatible import name used by older callers.
SendMessageRequest = ChatMessageRequest


class SourceMeta(BaseModel):
    source_type: Literal["doctype", "report", "tool"]
    source_name: str
    record_count: int | None = None
    filters: dict[str, Any] | None = None
    doctype: str | None = None
    report_name: str | None = None
    fields: list[str] | None = None


class PermissionMeta(BaseModel):
    allowed: bool = True
    risk_level: Literal["low", "medium", "high"] = "low"
    confirmation_required: bool = False
    filtered_fields: list[str] = Field(default_factory=list)
    blocked_fields: list[str] = Field(default_factory=list)
    reason: str | None = None


class TableColumn(BaseModel):
    key: str
    label: str
    type: str = "text"


class TablePart(BaseModel):
    type: Literal["table"] = "table"
    title: str
    columns: list[TableColumn]
    rows: list[dict[str, Any]]
    total_rows: int | None = None
    row_action: dict[str, Any] | None = None


class TextPart(BaseModel):
    type: Literal["text"] = "text"
    content: str


class ToolCallPart(BaseModel):
    type: Literal["tool_call"] = "tool_call"
    tool_name: str
    status: Literal["running", "success", "error"]
    input_summary: str | None = None
    output_summary: str | None = None


class ChartPart(BaseModel):
    type: Literal["chart"] = "chart"
    title: str
    chart_type: Literal["bar", "line", "pie", "donut", "area"]
    data: list[dict[str, Any]]
    x_key: str | None = None
    y_key: str | None = None


class FilePart(BaseModel):
    type: Literal["file"] = "file"
    file_id: str
    file_name: str
    file_type: str
    file_format: str
    mime_type: str
    download_url: str
    # Compatibility aliases for the existing React GeneratedFileCard contract.
    fileId: str
    fileName: str
    fileType: str
    fileFormat: str
    downloadUrl: str


class MissingFieldsPart(BaseModel):
    type: Literal["missing_fields"] = "missing_fields"
    doctype: str
    operation: Literal["create", "update"]
    fields: list[MissingField]
    collected_data: dict[str, Any] = Field(default_factory=dict)
    record_name: str | None = None
    conversation_id: str | None = None
    message_id: str | None = None


class RecordPreviewPart(BaseModel):
    type: Literal["record_preview"] = "record_preview"
    operation: Literal["create", "update"]
    doctype: str
    record_name: str | None = None
    before_data: dict[str, Any] | None = None
    after_data: dict[str, Any]
    risk_level: Literal["medium", "high"] = "medium"


class RecordDetailPart(BaseModel):
    type: Literal["record_detail"] = "record_detail"
    doctype: str
    name: str
    title: str | None = None
    status: str | None = None
    workflow_state: str | None = None
    docstatus: int | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, Any] = Field(default_factory=dict)
    items: list[dict[str, Any]] = Field(default_factory=list)
    available_workflow_actions: list[dict[str, Any]] = Field(default_factory=list)


class ConfirmationPart(BaseModel):
    type: Literal["confirmation"] = "confirmation"
    confirmation_id: str
    title: str
    description: str
    confirm_label: str = "Confirm"
    cancel_label: str = "Cancel"
    risk_level: Literal["medium", "high"] = "medium"


class SuggestedAction(BaseModel):
    label: str
    action_type: str
    disabled: bool = False
    reason: str | None = None


class ExtractionMeta(BaseModel):
    method: Literal["vertex_gemini", "rules"]
    confidence: float | None = None
    provider: str | None = None
    model: str | None = None
    privacy_checked: bool = False
    privacy_allowed: bool = False
    erp_data_sent: bool = False
    fallback_used: bool = False


MessagePart = TextPart | ToolCallPart | TablePart | ChartPart | FilePart | MissingFieldsPart | RecordPreviewPart | RecordDetailPart | ConfirmationPart


class AssistantChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: Literal["assistant"] = "assistant"
    intent: str
    parts: list[MessagePart]
    source: SourceMeta | None = None
    permission: PermissionMeta | None = None
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    suggestions: list[SuggestedPrompt] = Field(default_factory=list)
    extraction: ExtractionMeta | None = None
    # Temporary legacy fields for the current React ChatMessage contract.
    id: str
    content: str
    created_at: datetime


class ChatMessage(CamelModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    created_at: datetime
    parts: list[dict[str, Any]] = Field(default_factory=list)
    intent: str | None = None
    source: SourceMeta | None = None
    permission: PermissionMeta | None = None
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    suggestions: list[SuggestedPrompt] = Field(default_factory=list)
    extraction: ExtractionMeta | None = None


class ChatActionResult(CamelModel):
    action_id: str
    status: Literal["confirmed", "cancelled"]
