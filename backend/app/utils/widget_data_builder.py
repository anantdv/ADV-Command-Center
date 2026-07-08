from collections import defaultdict
from typing import Any

from app.config import settings
from app.core.exceptions import AppError, PermissionDenied
from app.frappe.client import FrappeClient
from app.schemas.dashboard import DashboardWidgetCreateRequest, DashboardWidgetData, DashboardWidgetLayout
from app.services.erpnext_service import ERPNextService
from app.services.report_service import ReportService
from app.utils.datetime import utc_now
from app.utils.table_formatter import build_table_part
from app.utils.chart_builder import infer_widget_chart_config, normalize_chart_widget_data
from app.utils.filter_normalizer import normalize_filters


class WidgetDataBuilder:
    """Rebuilds widget data from permission-aware ERP sources on every refresh."""

    def __init__(self, client: FrappeClient | None = None):
        self.client = client or FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name)
        self.erp = ERPNextService(self.client)
        self.reports = ReportService(self.client)

    async def build_widget_data(self, widget: DashboardWidgetCreateRequest | DashboardWidgetData | dict, cookies: dict | None = None, widget_id: str | None = None) -> DashboardWidgetData:
        raw = widget.model_dump() if hasattr(widget, "model_dump") else dict(widget)
        source = raw["source"]
        if hasattr(source, "model_dump"): source = source.model_dump()
        source_type = source["source_type"]
        source_name = source.get("doctype") or source.get("report_name") or source.get("source_name")
        if source_type not in {"doctype", "report"}:
            raise AppError("Only refreshable DocType and report sources can be pinned.", 422)
        fields = list(dict.fromkeys([*(source.get("fields") or []), source.get("group_by"), source.get("aggregate_field")]))
        fields = [field for field in fields if field]
        if source_type == "doctype":
            result = await self.erp.list_records(source_name, normalize_filters(source_name, source.get("filters") or {}), fields or ["name"], 500, cookies=cookies)
            permission = result.permissions.model_dump()
            if not permission.get("allowed", True): raise PermissionDenied(permission.get("reason") or "Dashboard source permission denied.")
            rows = result.records
        else:
            report = await self.reports.run_report(source_name, source.get("filters") or {}, cookies)
            rows = report.get("rows") or []
            permission = report.get("permission") or {"allowed": True, "risk_level": "low", "confirmation_required": False}
        data, chart_config = self._build(raw["widget_type"], raw["title"], rows, source, raw.get("chart_config"))
        value = data.get("value") if isinstance(data, dict) and "value" in data else None
        return DashboardWidgetData(widget_id=widget_id or raw.get("widget_id") or "preview", title=raw["title"], widget_type=raw["widget_type"], source=source, chart_config=chart_config, layout=raw.get("layout") or DashboardWidgetLayout(), data=data, permission=permission, last_refreshed_at=utc_now().isoformat(), refresh_interval_seconds=raw.get("refresh_interval_seconds", 300), visibility=raw.get("visibility", "private"), allowed_roles=raw.get("allowed_roles") or [], conversation_id=raw.get("conversation_id"), message_id=raw.get("message_id"), label=raw["title"], value=value)

    @staticmethod
    def _build(widget_type: str, title: str, rows: list[dict[str, Any]], source: dict[str, Any], chart_config: dict[str, Any] | None) -> tuple[dict | list, dict | None]:
        aggregate = source.get("aggregate_function")
        aggregate_field = source.get("aggregate_field")
        if widget_type in {"kpi", "summary_card"}:
            numbers = [WidgetDataBuilder._number(row.get(aggregate_field)) for row in rows] if aggregate_field else []
            numbers = [value for value in numbers if value is not None]
            if aggregate == "sum": value = sum(numbers)
            elif aggregate == "avg": value = sum(numbers) / len(numbers) if numbers else 0
            elif aggregate == "min": value = min(numbers) if numbers else 0
            elif aggregate == "max": value = max(numbers) if numbers else 0
            else: value = len(rows)
            return {"value": value, "label": title, "trend": None, "format": "currency" if aggregate_field and any(term in aggregate_field for term in ("amount", "total")) else "number", "subtitle": "Permission-aware ERPNext data"}, chart_config
        if widget_type == "table":
            table = build_table_part(title, rows, 20)
            return {"columns": [column.model_dump() for column in table.columns], "rows": table.rows, "total_rows": len(rows)}, chart_config
        group_by = source.get("group_by") or WidgetDataBuilder._category_key(rows)
        value_key = aggregate_field or "count"
        grouped: dict[str, float] = defaultdict(float)
        for row in rows:
            category = str(row.get(group_by) or "Unknown")
            grouped[category] += WidgetDataBuilder._number(row.get(aggregate_field)) or 1
        data = [{group_by: key, value_key: value} for key, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:12]]
        config = chart_config or infer_widget_chart_config(data, group_by, value_key)
        normalized = normalize_chart_widget_data(widget_type, data, config)
        return normalized["data"], normalized["chart_config"]

    @staticmethod
    def _category_key(rows: list[dict[str, Any]]) -> str:
        if not rows: return "category"
        for key in ("status", "customer", "supplier", "item_group", "posting_date", "name"):
            if key in rows[0]: return key
        return next(iter(rows[0]), "category")

    @staticmethod
    def _number(value: Any) -> float | None:
        if isinstance(value, bool) or value is None: return None
        if isinstance(value, (int, float)): return float(value)
        try: return float(str(value).replace("₹", "").replace(",", ""))
        except ValueError: return None
