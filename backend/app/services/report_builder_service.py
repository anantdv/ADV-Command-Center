from __future__ import annotations

from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.frappe.paths import RUN_REPORT
from app.schemas.report_builder import ReportColumn, ReportDiagnosticResponse, ReportRunWithColumnsRequest, ReportRunWithColumnsResponse
from app.services.erpnext_service import ERPNextService
from app.services.report_service import ReportService, default_report_filters
from app.utils.column_resolver import ColumnResolver
from app.utils.filter_normalizer import normalize_filters


class ReportBuilderService:
    def __init__(self, client: FrappeClient):
        self.client = client
        self.erp = ERPNextService(client)
        self.reports = ReportService(client)
        self.columns = ColumnResolver(client)

    async def available_columns(self, source_type: str, source_name: str, cookies: dict | None = None) -> list[ReportColumn]:
        return await self.columns.get_available_columns(source_type, source_name, cookies)

    async def run_with_columns(self, request: ReportRunWithColumnsRequest, cookies: dict | None = None) -> ReportRunWithColumnsResponse:
        selected = await self.columns.validate_selected_columns(request.source_type, request.source_name, request.columns, cookies)
        all_columns = await self.columns.get_available_columns(request.source_type, request.source_name, cookies)
        column_map = {column.key: column for column in all_columns}
        if request.source_type == "doctype":
            result = await self.erp.list_records(request.source_name, normalize_filters(request.source_name, request.filters), selected, request.limit, request.order_by, cookies)
            rows = [{key: row.get(key) for key in selected} for row in result.records]
            permission = result.permissions.model_dump()
        else:
            report = await self.reports.run_report(request.source_name, request.filters, cookies)
            rows = [_select(row, selected) for row in report.get("rows", [])[: request.limit]]
            permission = report.get("permission") or {"allowed": True}
        return ReportRunWithColumnsResponse(source_type=request.source_type, source_name=request.source_name, columns=[column_map.get(key) or ReportColumn(key=key, label=key.replace("_", " ").title()) for key in selected], rows=rows, total_rows=len(rows), permission=permission)

    async def diagnose(self, report_name: str, filters: dict[str, Any] | None = None, cookies: dict | None = None) -> ReportDiagnosticResponse:
        used_filters = await default_report_filters(report_name, filters or {}, self.erp, cookies)
        errors: list[str] = []
        recommendations: list[str] = []
        shape: dict[str, Any] = {}
        allowed: bool | None = None
        try:
            result = await self.reports.run_report(report_name, used_filters, cookies)
            columns = result.get("columns") or []
            rows = result.get("rows") or result.get("result") or []
            shape = {"has_columns": bool(columns), "has_rows": bool(rows), "row_count": len(rows)}
            allowed = bool((result.get("permission") or {"allowed": True}).get("allowed", True))
            if not columns:
                recommendations.append("Report returned no columns. Check companion report normalization.")
            if not rows:
                recommendations.append("No rows returned. This is not treated as a permission error.")
        except Exception as exc:
            errors.append(str(exc))
            allowed = False
        return ReportDiagnosticResponse(report_name=report_name, allowed_by_backend=True, allowed_by_frappe=allowed, method_path=RUN_REPORT, filters_used=used_filters, frappe_response_shape=shape, errors=errors, recommendations=recommendations)


def _select(row: dict[str, Any], selected: list[str]) -> dict[str, Any]:
    return {key: row.get(key) for key in selected}
