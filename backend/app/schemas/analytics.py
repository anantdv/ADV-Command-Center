from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from app.schemas.common import CamelModel


class AnalyticsPlanRequest(CamelModel):
    message: str


class AnalyticsRunRequest(CamelModel):
    analytics_key: str
    filters: dict[str, Any] | None = None
    date_range: dict[str, Any] | None = None
    chart_type: str | None = None
    limit: int | None = None


class AnalyticsPlanResponse(CamelModel):
    analytics_key: str | None = None
    title: str | None = None
    confidence: float = 0.0
    filters: dict[str, Any] = Field(default_factory=dict)
    date_range: dict[str, Any] | None = None
    chart_type: str | None = None
    limit: int | None = None


class AnalyticsResult(CamelModel):
    analytics_key: str
    title: str
    summary: str
    columns: list[dict[str, Any]]
    rows: list[dict[str, Any]]
    chart: dict[str, Any] | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    source: dict[str, Any] = Field(default_factory=dict)
    permission: dict[str, Any] | None = None
