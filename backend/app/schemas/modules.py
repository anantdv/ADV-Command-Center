from typing import Any, Literal

from pydantic import Field

from app.schemas.common import CamelModel, PermissionMeta


class ModuleSummary(CamelModel):
    slug: str
    name: str
    description: str
    metric: str
    metric_label: str
    color: str
    permissions: PermissionMeta


class ModuleDetail(CamelModel):
    module: ModuleSummary
    records: list[str]
    reports: list[str]


class ModuleRecords(CamelModel):
    records: list[dict[str, Any]]
    permissions: PermissionMeta


class ModuleReports(CamelModel):
    reports: list[str]
    permissions: PermissionMeta


class ERPModule(CamelModel):
    module_name: str
    label: str
    icon: str | None = None
    description: str | None = None
    category: str | None = None
    route: str
    enabled: bool = True
    accessible: bool = True
    doctypes: list[str] = Field(default_factory=list)


class ModuleKPI(CamelModel):
    id: str
    label: str
    value: int | float | str
    value_type: Literal["number", "currency", "percent", "text"] = "number"
    currency: str | None = None
    trend_label: str | None = None
    trend_value: float | None = None
    source_doctype: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    action_prompt: str | None = None


class ModuleReportCard(CamelModel):
    id: str
    title: str
    description: str | None = None
    report_type: Literal["table", "chart", "standard_report", "analytics"] = "table"
    source_doctype: str | None = None
    report_name: str | None = None
    chart_type: str | None = None
    data: list[dict[str, Any]] = Field(default_factory=list)
    columns: list[dict[str, Any]] = Field(default_factory=list)
    action_prompt: str | None = None


class ModuleRecentDocument(CamelModel):
    doctype: str
    name: str
    title: str | None = None
    status: str | None = None
    workflow_state: str | None = None
    party: str | None = None
    amount: float | None = None
    currency: str | None = None
    date: str | None = None
    modified: str | None = None


class ModuleDashboardResponse(CamelModel):
    module_name: str
    label: str
    kpis: list[ModuleKPI] = Field(default_factory=list)
    reports: list[ModuleReportCard] = Field(default_factory=list)
    recent_documents: list[ModuleRecentDocument] = Field(default_factory=list)
    quick_actions: list[dict[str, Any]] = Field(default_factory=list)
    permissions: dict[str, Any] = Field(default_factory=dict)
    doctypes: list[str] = Field(default_factory=list)
    pinned_widgets: list[dict[str, Any]] = Field(default_factory=list)


class ModuleDoctypeInfo(CamelModel):
    doctype: str
    label: str
    description: str | None = None
    icon: str | None = None
    can_read: bool = True
    can_create: bool = False
    record_count: int | None = None
    route: str
    default_fields: list[str] = Field(default_factory=list)


class ModuleDoctypeNavigationResponse(CamelModel):
    module_name: str
    doctypes: list[ModuleDoctypeInfo] = Field(default_factory=list)


class ModuleDoctypeRecordsResponse(CamelModel):
    module_name: str
    doctype: str
    page: int
    page_size: int
    total: int
    columns: list[dict[str, Any]] = Field(default_factory=list)
    rows: list[dict[str, Any]] = Field(default_factory=list)
