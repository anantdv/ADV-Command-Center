from datetime import datetime
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from app.schemas.common import CamelModel
from app.schemas.crud import MissingField
from app.schemas.entity_resolution import ChildRowsResolutionPart
from app.schemas.suggestions import SuggestedPrompt
from app.schemas.task_plan import PlanPart


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
    date_range: dict[str, str] | None = Field(
        default=None,
        validation_alias=AliasChoices("date_range", "dateRange"),
    )
    source: str | None = None
    parent_message_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("parent_message_id", "parentMessageId"),
    )
    active_report_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("active_report_id", "activeReportId"),
    )
    active_result_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("active_result_id", "activeResultId"),
    )
    current_filters: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices("current_filters", "currentFilters"),
    )
    selected_rows: list[dict[str, Any]] | None = Field(
        default=None,
        validation_alias=AliasChoices("selected_rows", "selectedRows"),
    )
    requested_output: str | None = Field(
        default=None,
        validation_alias=AliasChoices("requested_output", "requestedOutput"),
    )
    structured_action: dict[str, Any] | None = Field(
        default=None,
        validation_alias=AliasChoices("structured_action", "structuredAction"),
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
    result_id: str | None = None
    title: str
    columns: list[TableColumn]
    rows: list[dict[str, Any]]
    total_rows: int | None = None
    config: dict[str, Any] = Field(default_factory=dict)
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
    result_id: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    module: str | None = None
    title: str
    chart_type: Literal["bar", "line", "pie", "donut", "area"]
    data: list[dict[str, Any]]
    x_key: str | None = None
    y_key: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    available_actions: list[str] = Field(default_factory=list)


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
    draft_session_id: str | None = None
    draft_version: int | None = None
    record_name: str | None = None
    before_data: dict[str, Any] | None = None
    after_data: dict[str, Any]
    totals: dict[str, Any] = Field(default_factory=dict)
    changes: list[dict[str, Any]] = Field(default_factory=list)
    risk_level: Literal["medium", "high"] = "medium"


class DraftInspectionSection(BaseModel):
    title: str
    rows: list[dict[str, Any]] = Field(default_factory=list)


class DraftInspectionPart(BaseModel):
    type: Literal["draft_inspection"] = "draft_inspection"
    draft_session_id: str
    doctype: str
    draft_version: int | None = None
    fields: dict[str, Any] = Field(default_factory=dict)
    sections: list[DraftInspectionSection] = Field(default_factory=list)
    mutation_performed: bool = False


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


class DraftFieldOption(BaseModel):
    value: str
    label: str
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    disabled: bool = False
    reason: str | None = None


class DraftFieldOptionsPart(BaseModel):
    type: Literal["draft_field_options"] = "draft_field_options"
    draft_session_id: str
    doctype: str
    fieldname: str
    label: str
    table_field: str | None = None
    row_ids: list[str] = Field(default_factory=list)
    message: str
    options: list[DraftFieldOption] = Field(default_factory=list)


class ConfirmationPart(BaseModel):
    type: Literal["confirmation"] = "confirmation"
    confirmation_id: str
    title: str
    description: str
    confirm_label: str = "Confirm"
    cancel_label: str = "Cancel"
    risk_level: Literal["medium", "high"] = "medium"


class WorkflowConfirmationPart(BaseModel):
    type: Literal["workflow_confirmation"] = "workflow_confirmation"
    doctype: str
    name: str
    action: str
    current_state: str | None = None
    next_state: str | None = None
    title: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    confirmation_id: str


class OCRMappingPreviewPart(BaseModel):
    type: Literal["ocr_mapping_preview"] = "ocr_mapping_preview"
    intake_id: str
    source_document_type: str
    target_doctype: str
    extracted_fields: dict[str, Any] = Field(default_factory=dict)
    draft_payload: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confirmation_required: bool = True
    confirmation_id: str | None = None


class SuggestedAction(BaseModel):
    label: str
    action_type: str
    disabled: bool = False
    reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ExtractionMeta(BaseModel):
    method: Literal["vertex_gemini", "rules"]
    confidence: float | None = None
    provider: str | None = None
    model: str | None = None
    privacy_checked: bool = False
    privacy_allowed: bool = False
    erp_data_sent: bool = False
    fallback_used: bool = False


MessagePart = TextPart | ToolCallPart | TablePart | ChartPart | FilePart | MissingFieldsPart | RecordPreviewPart | DraftInspectionPart | RecordDetailPart | DraftFieldOptionsPart | ConfirmationPart | WorkflowConfirmationPart | OCRMappingPreviewPart | ChildRowsResolutionPart | PlanPart


class AssistantChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    role: Literal["assistant"] = "assistant"
    intent: str
    response_type: str | None = None
    current_state: str | None = None
    next_expected_action: str | None = None
    available_actions: list[str] = Field(default_factory=list)
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
    response_type: str | None = None
    current_state: str | None = None
    next_expected_action: str | None = None
    available_actions: list[str] = Field(default_factory=list)
    source: SourceMeta | None = None
    permission: PermissionMeta | None = None
    suggested_actions: list[SuggestedAction] = Field(default_factory=list)
    suggestions: list[SuggestedPrompt] = Field(default_factory=list)
    extraction: ExtractionMeta | None = None


class ChatActionResult(CamelModel):
    action_id: str
    status: Literal["confirmed", "cancelled"]
