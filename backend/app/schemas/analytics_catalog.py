from __future__ import annotations

from typing import Any, Literal

from pydantic import Field

from app.schemas.common import CamelModel


class AnalyticsMetric(CamelModel):
    field: str
    function: Literal["count", "sum", "avg", "min", "max"]
    label: str


class AnalyticsDefinition(CamelModel):
    key: str
    title: str
    description: str | None = None
    module: str
    source_type: Literal["doctype", "standard_report", "composite"] = "doctype"
    source_name: str
    date_field: str | None = None
    group_by: list[str] = Field(default_factory=list)
    metrics: list[AnalyticsMetric] = Field(default_factory=list)
    filters: dict[str, Any] = Field(default_factory=dict)
    default_chart: Literal["bar", "line", "pie", "donut", "area", "table"] = "table"
    default_limit: int = 20
    required_fields: list[str] = Field(default_factory=list)
    drilldown_doctype: str | None = None
    drilldown_filters: dict[str, Any] = Field(default_factory=dict)
    supports_export: bool = True
    supports_pin: bool = True
