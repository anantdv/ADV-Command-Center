from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


AggregationFunction = Literal["count", "sum", "avg", "min", "max"]
ChartType = Literal["bar", "line", "pie", "donut", "area", "table"]
TimeGrain = Literal["day", "week", "month", "quarter", "year"]


class AggregationMetric(BaseModel):
    field: str
    function: AggregationFunction
    label: str | None = None


class AggregationPlan(BaseModel):
    enabled: bool = False
    source_type: Literal["doctype", "report"] = "doctype"
    source_name: str
    filters: dict[str, Any] = Field(default_factory=dict)
    fields: list[str] = Field(default_factory=list)
    group_by: list[str] = Field(default_factory=list)
    metrics: list[AggregationMetric] = Field(default_factory=list)
    time_field: str | None = None
    time_grain: TimeGrain | None = None
    order_by_metric: str | None = None
    order_direction: Literal["asc", "desc"] = "desc"
    limit: int = 20
    chart_type: ChartType = "table"
    chart_title: str | None = None
    confidence: float = 0.0
    missing_information: list[str] = Field(default_factory=list)
    normalized_filters: dict[str, Any] = Field(default_factory=dict)


class AggregationResult(BaseModel):
    plan: AggregationPlan
    columns: list[dict[str, Any]]
    rows: list[dict[str, Any]]
    chart: dict[str, Any] | None = None
    summary: str
    source: dict[str, Any]
    permission: dict[str, Any] | None = None
