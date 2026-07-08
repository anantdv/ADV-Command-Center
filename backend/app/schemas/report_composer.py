from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import CamelModel


ReportSourceType = Literal["doctype", "standard_report"]
ReportOutputMode = Literal["detail", "summary", "chart", "table_chart"]
ReportChartType = Literal["none", "bar", "line", "pie", "donut", "area"]
ReportAggregationFunction = Literal["count", "sum", "avg", "min", "max"]


class ReportSource(CamelModel):
    source_type: ReportSourceType = "doctype"
    source_name: str


class ReportSelectedField(CamelModel):
    fieldname: str
    label: str | None = None
    fieldtype: str | None = None
    visible: bool = True


class ReportMetric(CamelModel):
    fieldname: str
    function: ReportAggregationFunction
    label: str | None = None
    output_key: str | None = None


class ReportFilter(CamelModel):
    fieldname: str
    operator: Literal["=", "!=", ">", "<", ">=", "<=", "in", "not in", "like", "between"]
    value: Any


class ReportSort(CamelModel):
    fieldname: str
    direction: Literal["asc", "desc"] = "desc"


class ReportChartConfig(CamelModel):
    chart_type: ReportChartType = "none"
    x_key: str | None = None
    y_key: str | None = None
    name_key: str | None = None
    value_key: str | None = None
    title: str | None = None


class ReportComposerPlan(CamelModel):
    title: str | None = None
    description: str | None = None
    source: ReportSource
    output_mode: ReportOutputMode = "detail"
    fields: list[ReportSelectedField] = Field(default_factory=list)
    filters: list[ReportFilter] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    metrics: list[ReportMetric] = Field(default_factory=list)
    sort: list[ReportSort] = Field(default_factory=list)
    limit: int = 100
    chart: ReportChartConfig = Field(default_factory=ReportChartConfig)
    date_range: dict[str, Any] | None = None
    confidence: float = 0.0
    missing_information: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    view_name: str | None = None


class ReportComposerPlanRequest(CamelModel):
    message: str
    module_context: str | None = None


class ReportComposerRunRequest(CamelModel):
    plan: ReportComposerPlan


class ReportComposerResult(CamelModel):
    plan: ReportComposerPlan
    columns: list[dict[str, Any]]
    rows: list[dict[str, Any]]
    chart: dict[str, Any] | None = None
    summary: str
    filters_applied: dict[str, Any] = Field(default_factory=dict)
    source_metadata: dict[str, Any] = Field(default_factory=dict)
    permission: dict[str, Any] | None = None


class SaveReportViewRequest(CamelModel):
    name: str
    description: str | None = None
    plan: ReportComposerPlan
    visibility: Literal["private", "role_based"] = "private"
    allowed_roles: list[str] = Field(default_factory=list)


class SavedReportView(CamelModel):
    view_id: str
    name: str
    description: str | None = None
    plan: ReportComposerPlan
    visibility: str = "private"
    allowed_roles: list[str] = Field(default_factory=list)
    created_by: str
    created_at: str
    updated_at: str | None = None


class ReportComposerDebugResponse(CamelModel):
    plan: ReportComposerPlan
    validated_plan: ReportComposerPlan
    normalized_filters: dict[str, Any]
    required_source_fields: list[str]
    warnings: list[str] = Field(default_factory=list)
