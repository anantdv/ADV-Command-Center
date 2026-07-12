from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

CommandIntentType = Literal[
    "list_records",
    "get_record_detail",
    "run_report",
    "run_analytics",
    "generate_chart",
    "report_composer",
    "workflow_list_pending",
    "workflow_get_detail",
    "workflow_apply_action",
    "crud_create_draft",
    "crud_update_draft",
    "ocr_intake",
    "export_result",
    "pin_result",
    "unsupported",
]


class CommandIntent(BaseModel):
    intent: CommandIntentType
    confidence: float = 0.0
    source: Literal["hard_rule", "llm", "hybrid", "button", "fallback"] = "fallback"
    message: str
    module_context: str | None = None
    doctype: str | None = None
    record_name: str | None = None
    report_name: str | None = None
    analytics_key: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    date_range: dict[str, Any] | None = None
    chart_requested: bool = False
    chart_type: str | None = None
    explicit_context_reference: bool = False
    uses_previous_result: bool = False
    previous_message_id: str | None = None
    action_payload: dict[str, Any] = Field(default_factory=dict)
    warnings: list[str] = Field(default_factory=list)
    missing_information: list[str] = Field(default_factory=list)
