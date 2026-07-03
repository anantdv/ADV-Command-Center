from typing import Any, Literal

from pydantic import BaseModel, Field

AllowedIntent = Literal["list_records", "get_record", "run_report", "generate_file", "pin_to_dashboard", "crud_create", "crud_update", "blocked_write", "unsupported"]


class ExtractedIntent(BaseModel):
    intent: AllowedIntent
    operation: Literal["read", "create", "update", "export", "pin", "support", "blocked", "none"] = "none"
    doctype: str | None = None
    report_name: str | None = None
    record_name: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)
    filters: dict[str, Any] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    file_format: Literal["xlsx", "csv", "pdf", "html", "png"] | None = None
    widget_type: Literal["kpi", "line_chart", "bar_chart", "pie_chart", "donut_chart", "area_chart", "table", "summary_card"] | None = None
    date_range: dict[str, str] | None = None
    limit: int = 20
    confidence: float = 0.0
    missing_information: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None
    user_facing_summary: str | None = None
    extraction_method: Literal["vertex_gemini", "rules"] | None = None
    provider: str | None = None
    model: str | None = None
    latency_ms: int | None = None
    privacy_checked: bool = False
    privacy_allowed: bool = False
    erp_data_sent: bool = False
    fallback_used: bool = False


def get_extracted_intent_json_schema() -> dict:
    schema = ExtractedIntent.model_json_schema()
    # Provider response schemas do not need local-only extraction metadata.
    for field in (
        "extraction_method", "provider", "model", "latency_ms",
        "privacy_checked", "privacy_allowed", "erp_data_sent", "fallback_used",
    ):
        schema.get("properties", {}).pop(field, None)
    return schema
