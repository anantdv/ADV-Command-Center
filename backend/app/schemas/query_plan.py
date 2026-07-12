from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.aggregation import AggregationPlan


QueryIntent = Literal[
    "list_records",
    "get_record",
    "run_report",
    "generate_file",
    "pin_to_dashboard",
    "crud_create",
    "crud_update",
    "blocked_write",
    "unsupported",
]


class QueryPlan(BaseModel):
    """Safe intermediate representation for a natural language ERP query.

    A QueryPlan is not an execution authorization. It is only a normalized plan
    that still has to pass through the ERP/Frappe access-controlled services.
    """

    intent: QueryIntent
    operation: Literal["read", "create", "update", "export", "pin", "blocked", "none"] = "none"

    doctype: str | None = None
    report_name: str | None = None
    record_name: str | None = None

    filters: dict[str, Any] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    date_range: dict[str, Any] | None = None

    order_by: str | None = None
    limit: int = 50

    data: dict[str, Any] = Field(default_factory=dict)
    file_format: Literal["xlsx", "csv", "pdf", "html", "png"] | None = None
    widget_type: str | None = None

    confidence: float = 0.0
    missing_information: list[str] = Field(default_factory=list)
    blocked_reason: str | None = None
    user_facing_summary: str | None = None

    extraction_method: Literal["vertex_gemini", "rules", "hybrid"] = "rules"
    normalized_filters: dict[str, Any] = Field(default_factory=dict)
    permission_checked: bool = False
    aggregation: AggregationPlan | None = None
    expects_chart: bool = False
    expects_aggregation: bool = False
