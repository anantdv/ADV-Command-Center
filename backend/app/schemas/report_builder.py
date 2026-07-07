from typing import Any, Literal

from pydantic import BaseModel, Field


class ReportColumn(BaseModel):
    key: str
    label: str
    fieldtype: str = "Data"
    visible: bool = True
    source: Literal["doctype", "report", "computed"] = "doctype"


class ReportColumnConfigRequest(BaseModel):
    source_type: Literal["doctype", "report"]
    source_name: str
    selected_columns: list[str] = Field(default_factory=list)
    removed_columns: list[str] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    limit: int = Field(100, ge=1, le=500)


class ReportRunWithColumnsRequest(BaseModel):
    source_type: Literal["doctype", "report"]
    source_name: str
    filters: dict[str, Any] = Field(default_factory=dict)
    columns: list[str] = Field(default_factory=list)
    limit: int = Field(100, ge=1, le=500)
    order_by: str | None = None


class ReportRunWithColumnsResponse(BaseModel):
    source_type: str
    source_name: str
    columns: list[ReportColumn]
    rows: list[dict[str, Any]]
    total_rows: int
    permission: dict[str, Any] | None = None


class ReportDiagnosticRequest(BaseModel):
    report_name: str
    filters: dict[str, Any] = Field(default_factory=dict)


class ReportDiagnosticResponse(BaseModel):
    report_name: str
    allowed_by_backend: bool
    allowed_by_frappe: bool | None = None
    method_path: str
    filters_used: dict[str, Any]
    frappe_response_shape: dict[str, Any] = Field(default_factory=dict)
    errors: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
