from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError
from app.schemas.aggregation import AggregationMetric, AggregationPlan
from app.schemas.analytics import AnalyticsPlanResponse, AnalyticsResult
from app.schemas.analytics_catalog import AnalyticsDefinition
from app.services.aggregation_service import AggregationService
from app.services.analytics_catalog_service import AnalyticsCatalogService, analytics_catalog_service
from app.services.report_service import ReportService
from app.frappe.client import FrappeClient
from app.services.erpnext_service import ERPNextService
from app.utils.analytics_catalog import ANALYTICS_CATALOG
from app.utils.analytics_plan_builder import AnalyticsPlanBuilder
from app.utils.filter_normalizer import normalize_filters
from app.utils.ids import new_id


class AnalyticsService:
    def __init__(self, aggregation: AggregationService | None = None, planner: AnalyticsPlanBuilder | None = None, catalog: AnalyticsCatalogService | None = None):
        self.aggregation = aggregation or AggregationService()
        self.planner = planner or AnalyticsPlanBuilder()
        self.catalog_service = catalog or analytics_catalog_service

    async def catalog(self, user: str = "unknown", module: str | None = None, cookies: dict | None = None) -> dict[str, dict[str, Any]]:
        await self._audit("analytics_catalog_viewed", user, None, True)
        items = await self.catalog_service.list_accessible_catalog(module, cookies)
        return {item.key: item.model_dump(mode="json") for item in items}

    async def plan(self, message: str, user: str = "unknown") -> AnalyticsPlanResponse:
        result = self.planner.build_from_prompt(message)
        await self._audit("analytics_plan_created", user, result.analytics_key, bool(result.analytics_key), output=result.title)
        return result

    async def run_analytics(self, analytics_key: str, filters: dict | None = None, date_range: dict | None = None, chart_type: str | None = None, limit: int | None = None, cookies: dict | None = None, user: str = "unknown") -> AnalyticsResult:
        if not settings.enable_analytics:
            raise AppError("Analytics are disabled.", 503)
        raw_definition = ANALYTICS_CATALOG.get(analytics_key)
        if not raw_definition:
            raise AppError("Unsupported analytics report.", 404, {"analytics_key": analytics_key})
        definition = AnalyticsDefinition(**raw_definition)
        await self._audit("analytics_run_started", user, analytics_key, True)
        if definition.source_type == "standard_report":
            result = await self._run_standard_report(definition, filters or {}, date_range, chart_type, limit, cookies)
        elif definition.source_type == "composite":
            result = await self._run_composite(definition, filters or {}, date_range, chart_type, limit, cookies)
        else:
            result = await self._run_doctype(definition, filters or {}, date_range, chart_type, limit, cookies, user)
        await self._audit("analytics_run_completed", user, analytics_key, True, row_count=len(result.rows), output=result.summary)
        return result

    async def _run_doctype(self, definition: AnalyticsDefinition, filters: dict[str, Any], date_range: dict | None, chart_type: str | None, limit: int | None, cookies: dict | None, user: str) -> AnalyticsResult:
        metric_defs = [metric.model_dump() for metric in definition.metrics]
        group_by = [] if definition.group_by == ["month"] else list(definition.group_by or [])
        time_field = definition.date_field if definition.group_by == ["month"] else None
        combined_filters = {**definition.filters, **(filters or {})}
        plan = AggregationPlan(
            enabled=True,
            source_name=definition.source_name,
            filters=normalize_filters(definition.source_name, combined_filters, date_range),
            fields=definition.required_fields,
            group_by=group_by,
            metrics=[AggregationMetric(**metric) for metric in metric_defs],
            time_field=time_field,
            time_grain="month" if time_field else None,
            order_by_metric=f"{metric_defs[0]['field']}_{metric_defs[0]['function']}",
            limit=limit or settings.analytics_default_limit,
            chart_type=chart_type or definition.default_chart,
            chart_title=definition.title,
        )
        result = await self.aggregation.run_aggregation(plan, cookies, user)
        drilldown = _drilldown(definition, result.source.get("filters") or {}, date_range)
        return AnalyticsResult(analytics_key=definition.key, title=definition.title, summary=result.summary, columns=result.columns, rows=result.rows, chart=result.chart, filters=result.source.get("filters") or {}, filters_applied=result.source.get("filters") or {}, source=result.source, permission=result.permission, drilldown=drilldown, result_id=new_id("analytics"))

    async def _run_standard_report(self, definition: AnalyticsDefinition, filters: dict[str, Any], date_range: dict | None, chart_type: str | None, limit: int | None, cookies: dict | None) -> AnalyticsResult:
        report = ReportService(_client())
        used_filters = _report_filters(filters, date_range)
        try:
            data = await report.run_report(definition.source_name, used_filters, cookies)
        except Exception as exc:
            raise AppError(f"This ERPNext report could not be run safely: {definition.source_name}.", 422, {"report": definition.source_name, "reason": str(exc)}) from exc
        rows = list(data.get("rows") or data.get("result") or [])[: (limit or settings.analytics_default_limit)]
        columns = _columns_from_report(data.get("columns") or [], rows)
        chart = _chart_from_rows(definition.title, rows, chart_type or definition.default_chart)
        summary = f"I loaded {len(rows)} row{'s' if len(rows) != 1 else ''} from {definition.source_name}."
        return AnalyticsResult(analytics_key=definition.key, title=definition.title, summary=summary, columns=columns, rows=rows, chart=chart, filters=used_filters, filters_applied=used_filters, source={"source_type": "standard_report", "source_name": definition.source_name, "filters": used_filters}, permission=data.get("permission") or {"allowed": True, "risk_level": "low"}, drilldown=None, result_id=new_id("analytics"))

    async def _run_composite(self, definition: AnalyticsDefinition, filters: dict[str, Any], date_range: dict | None, chart_type: str | None, limit: int | None, cookies: dict | None) -> AnalyticsResult:
        if definition.key != "monthly_sales_vs_purchase":
            raise AppError("Unsupported composite analytics.", 404, {"analytics_key": definition.key})
        erp = ERPNextService(_client())
        sales = (await erp.list_records("Sales Invoice", {}, ["name", "posting_date", "grand_total"], settings.analytics_max_source_rows, cookies=cookies, date_range=date_range)).records
        purchases = (await erp.list_records("Purchase Invoice", {}, ["name", "posting_date", "grand_total"], settings.analytics_max_source_rows, cookies=cookies, date_range=date_range)).records
        merged: dict[str, dict[str, Any]] = defaultdict(lambda: {"period": "Unknown", "_sort": "9999-99", "sales_total": 0.0, "purchase_total": 0.0})
        for row in sales:
            key, label = _month(row.get("posting_date"))
            merged[key].update({"period": label, "_sort": key})
            merged[key]["sales_total"] += _number(row.get("grand_total"))
        for row in purchases:
            key, label = _month(row.get("posting_date"))
            merged[key].update({"period": label, "_sort": key})
            merged[key]["purchase_total"] += _number(row.get("grand_total"))
        rows = sorted(merged.values(), key=lambda row: row["_sort"])[: (limit or 24)]
        for row in rows:
            row.pop("_sort", None)
        chart = {"chart_type": chart_type or "line", "title": definition.title, "x_key": "period", "series": [{"data_key": "sales_total", "label": "Sales"}, {"data_key": "purchase_total", "label": "Purchase"}], "data": rows}
        columns = [{"key": "period", "label": "Period"}, {"key": "sales_total", "label": "Sales"}, {"key": "purchase_total", "label": "Purchase"}]
        return AnalyticsResult(analytics_key=definition.key, title=definition.title, summary=f"I compared sales and purchase totals across {len(rows)} month{'s' if len(rows) != 1 else ''}.", columns=columns, rows=rows, chart=chart, filters=date_range or {}, filters_applied=date_range or {}, source={"source_type": "composite", "source_name": definition.source_name, "filters": date_range or {}}, permission={"allowed": True, "risk_level": "low"}, drilldown=None, result_id=new_id("analytics"))

    @staticmethod
    async def _audit(action: str, user: str, analytics_key: str | None, allowed: bool, row_count: int | None = None, output: str | None = None) -> None:
        await log_audit_event(AuditEvent(user=user, action=action, agent_name="analytics_agent", tool_name="run_analytics", allowed=allowed, risk_level="low", input_summary=analytics_key, output_summary=output, record_count=row_count, erp_data_sent=False))


analytics_service = AnalyticsService()


def _client() -> FrappeClient:
    return FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name)


def _report_filters(filters: dict[str, Any], date_range: dict | None) -> dict[str, Any]:
    output = dict(filters or {})
    if date_range:
        output.setdefault("from_date", date_range.get("from_date"))
        output.setdefault("to_date", date_range.get("to_date"))
    return {key: value for key, value in output.items() if value not in (None, "")}


def _columns_from_report(columns: list[Any], rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for index, column in enumerate(columns or []):
        if isinstance(column, dict):
            key = column.get("fieldname") or column.get("key") or column.get("label") or f"col_{index}"
            output.append({"key": str(key), "label": str(column.get("label") or key)})
        else:
            key = str(column).split(":")[0] or f"col_{index}"
            output.append({"key": key, "label": key.replace("_", " ").title()})
    if not output and rows:
        output = [{"key": key, "label": key.replace("_", " ").title()} for key in rows[0].keys()]
    return output


def _chart_from_rows(title: str, rows: list[dict[str, Any]], chart_type: str) -> dict[str, Any] | None:
    if chart_type == "table" or not rows:
        return None
    keys = list(rows[0].keys())
    x_key = next((key for key in keys if not isinstance(rows[0].get(key), (int, float))), keys[0])
    y_key = next((key for key in keys if isinstance(rows[0].get(key), (int, float))), None)
    if not y_key:
        return None
    return {"chart_type": chart_type, "title": title, "x_key": x_key, "y_key": y_key, "series": [{"data_key": y_key, "label": y_key.replace("_", " ").title()}], "data": rows}


def _drilldown(definition: AnalyticsDefinition, filters: dict[str, Any], date_range: dict | None) -> dict[str, Any] | None:
    if not definition.drilldown_doctype:
        return None
    return {"type": "module_list", "module": definition.module, "doctype": definition.drilldown_doctype, "base_filters": filters, "date_range": date_range, "group_field": next((field for field in definition.group_by if field != "month"), None)}


def _number(value: Any) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace(",", "").replace("₹", "").strip())
        except ValueError:
            return 0.0
    return 0.0


def _month(value: Any) -> tuple[str, str]:
    try:
        parsed = date.fromisoformat(str(value)[:10])
    except Exception:
        return "9999-99", "Unknown"
    return parsed.strftime("%Y-%m"), parsed.strftime("%b %Y")
