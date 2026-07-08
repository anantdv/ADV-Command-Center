from __future__ import annotations

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError
from app.schemas.aggregation import AggregationMetric, AggregationPlan
from app.schemas.analytics import AnalyticsPlanResponse, AnalyticsResult
from app.services.aggregation_service import AggregationService
from app.utils.analytics_catalog import ANALYTICS_CATALOG
from app.utils.analytics_plan_builder import AnalyticsPlanBuilder
from app.utils.filter_normalizer import normalize_filters


class AnalyticsService:
    def __init__(self, aggregation: AggregationService | None = None, planner: AnalyticsPlanBuilder | None = None):
        self.aggregation = aggregation or AggregationService()
        self.planner = planner or AnalyticsPlanBuilder()

    async def catalog(self, user: str = "unknown") -> dict:
        await self._audit("analytics_catalog_viewed", user, None, True)
        return ANALYTICS_CATALOG

    async def plan(self, message: str, user: str = "unknown") -> AnalyticsPlanResponse:
        result = self.planner.build_from_prompt(message)
        await self._audit("analytics_plan_created", user, result.analytics_key, bool(result.analytics_key), output=result.title)
        return result

    async def run_analytics(self, analytics_key: str, filters: dict | None = None, date_range: dict | None = None, chart_type: str | None = None, limit: int | None = None, cookies: dict | None = None, user: str = "unknown") -> AnalyticsResult:
        if not settings.enable_analytics:
            raise AppError("Analytics are disabled.", 503)
        definition = ANALYTICS_CATALOG.get(analytics_key)
        if not definition:
            raise AppError("Unsupported analytics report.", 404, {"analytics_key": analytics_key})
        await self._audit("analytics_run_started", user, analytics_key, True)
        source_name = definition["source_name"]
        metric_defs = definition["metrics"]
        group_by = [] if definition.get("group_by") == ["month"] else list(definition.get("group_by") or [])
        time_field = definition.get("date_field") if definition.get("group_by") == ["month"] else None
        plan = AggregationPlan(
            enabled=True,
            source_name=source_name,
            filters=normalize_filters(source_name, filters or {}, date_range),
            fields=definition["required_fields"],
            group_by=group_by,
            metrics=[AggregationMetric(**metric) for metric in metric_defs],
            time_field=time_field,
            time_grain="month" if time_field else None,
            order_by_metric=f"{metric_defs[0]['field']}_{metric_defs[0]['function']}",
            limit=limit or settings.analytics_default_limit,
            chart_type=chart_type or definition["default_chart"],
            chart_title=definition["title"],
        )
        result = await self.aggregation.run_aggregation(plan, cookies, user)
        await self._audit("analytics_run_completed", user, analytics_key, True, row_count=len(result.rows), output=result.summary)
        return AnalyticsResult(analytics_key=analytics_key, title=definition["title"], summary=result.summary, columns=result.columns, rows=result.rows, chart=result.chart, filters=result.source.get("filters") or {}, source=result.source, permission=result.permission)

    @staticmethod
    async def _audit(action: str, user: str, analytics_key: str | None, allowed: bool, row_count: int | None = None, output: str | None = None) -> None:
        await log_audit_event(AuditEvent(user=user, action=action, agent_name="analytics_agent", tool_name="run_analytics", allowed=allowed, risk_level="low", input_summary=analytics_key, output_summary=output, record_count=row_count, erp_data_sent=False))


analytics_service = AnalyticsService()
