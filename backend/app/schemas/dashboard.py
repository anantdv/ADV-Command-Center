from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

WidgetType = Literal["kpi", "line_chart", "bar_chart", "pie_chart", "donut_chart", "area_chart", "table", "aging", "summary_card"]
SourceType = Literal["doctype", "report", "chat_result", "manual_config"]
SENSITIVE_FIELD_PARTS = ("password", "secret", "token", "api_key", "api_secret", "otp", "bank", "account_no", "salary", "pan", "aadhaar")


class DashboardWidgetSource(BaseModel):
    source_type: SourceType
    source_name: str | None = None
    doctype: str | None = None
    report_name: str | None = None
    filters: dict[str, Any] | None = None
    fields: list[str] | None = None
    group_by: str | None = None
    aggregate_field: str | None = None
    aggregate_function: Literal["count", "sum", "avg", "min", "max"] | None = None

    @model_validator(mode="after")
    def validate_source(self):
        if self.source_type == "doctype" and not (self.doctype or self.source_name):
            raise ValueError("doctype is required for a DocType widget")
        if self.source_type == "report" and not (self.report_name or self.source_name):
            raise ValueError("report_name is required for a report widget")
        values = [*(self.fields or []), self.group_by or "", self.aggregate_field or ""]
        if any(any(term in value.lower() for term in SENSITIVE_FIELD_PARTS) for value in values):
            raise ValueError("Sensitive fields cannot be used in dashboard widgets")
        serialized = " ".join([self.source_name or "", self.doctype or "", self.report_name or "", *(self.fields or []), str(self.filters or {})]).lower()
        if any(term in serialized for term in ("select ", " drop ", " union ", "--", ";")):
            raise ValueError("Raw SQL is not supported in dashboard widgets")
        return self

    def resolved_name(self) -> str:
        return self.doctype or self.report_name or self.source_name or "Manual"


class DashboardWidgetLayout(BaseModel):
    x: int = Field(0, ge=0, le=24)
    y: int = Field(0, ge=0, le=1000)
    w: int = Field(4, ge=2, le=12)
    h: int = Field(3, ge=2, le=12)


class DashboardWidgetCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    widget_type: WidgetType
    source: DashboardWidgetSource
    chart_config: dict[str, Any] | None = None
    layout: DashboardWidgetLayout | None = None
    refresh_interval_seconds: int | None = Field(300, ge=30, le=86400)
    visibility: Literal["private", "role_based"] = "private"
    allowed_roles: list[str] = Field(default_factory=list)
    conversation_id: str | None = None
    message_id: str | None = None
    target_type: Literal["overview", "module"] = "overview"
    module_name: str | None = None

    @field_validator("chart_config")
    @classmethod
    def reject_embedded_chart_rows(cls, value: dict[str, Any] | None):
        if value and any(key.lower() in {"data", "rows", "records"} for key in value):
            raise ValueError("Widget metadata cannot contain raw result rows")
        return value


class DashboardWidgetUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=160)
    widget_type: WidgetType | None = None
    chart_config: dict[str, Any] | None = None
    layout: DashboardWidgetLayout | None = None
    refresh_interval_seconds: int | None = Field(default=None, ge=30, le=86400)
    visibility: Literal["private", "role_based"] | None = None
    allowed_roles: list[str] | None = None

    @field_validator("chart_config")
    @classmethod
    def reject_embedded_chart_rows(cls, value: dict[str, Any] | None):
        if value and any(key.lower() in {"data", "rows", "records"} for key in value):
            raise ValueError("Widget metadata cannot contain raw result rows")
        return value


class DashboardWidgetData(BaseModel):
    widget_id: str
    title: str
    widget_type: WidgetType
    source: DashboardWidgetSource
    chart_config: dict[str, Any] | None = None
    layout: DashboardWidgetLayout = Field(default_factory=DashboardWidgetLayout)
    data: dict[str, Any] | list[dict[str, Any]] | None = None
    permission: dict[str, Any] | None = None
    last_refreshed_at: str | None = None
    error: str | None = None
    refresh_interval_seconds: int | None = 300
    visibility: Literal["private", "role_based"] = "private"
    allowed_roles: list[str] = Field(default_factory=list)
    conversation_id: str | None = None
    message_id: str | None = None
    target_type: Literal["overview", "module"] = "overview"
    module_name: str | None = None
    # Backward-compatible KPI presentation fields.
    label: str | None = None
    value: str | int | float | None = None
    change: str | None = None
    trend: Literal["up", "down"] | None = None
    accent: str = "indigo"


class DashboardOverviewResponse(BaseModel):
    kpis: list[DashboardWidgetData]
    widgets: list[DashboardWidgetData]
    insights: list[str] = Field(default_factory=list)
    # Legacy chart arrays remain during the frontend migration.
    sales_trend: list[dict[str, Any]] = Field(default_factory=list)
    cash_flow: list[dict[str, Any]] = Field(default_factory=list)
    top_customers: list[dict[str, Any]] = Field(default_factory=list)
    aging: list[dict[str, Any]] = Field(default_factory=list)


class DashboardWidgetReorderRequest(BaseModel):
    layouts: list[dict[str, Any]]


class PinChatResultRequest(BaseModel):
    conversation_id: str
    message_id: str
    title: str = Field(min_length=1, max_length=160)
    widget_type: WidgetType
    source: DashboardWidgetSource
    chart_config: dict[str, Any] | None = None
    target_type: Literal["overview", "module"] = "overview"
    module_name: str | None = None


class PinChatResultResponse(BaseModel):
    widget_id: str
    title: str
    message: str = "Pinned to Overview successfully."
