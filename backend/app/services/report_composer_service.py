from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError, PermissionDenied
from app.frappe.client import FrappeClient
from app.schemas.report_composer import (
    ReportComposerPlan,
    ReportComposerPlanRequest,
    ReportComposerResult,
    ReportComposerRunRequest,
    SaveReportViewRequest,
    SavedReportView,
)
from app.services.erpnext_service import ERPNextService
from app.utils.report_aggregation_engine import ReportAggregationEngine
from app.utils.report_chart_builder import build_chart_from_report_result
from app.utils.report_composer_planner import ReportComposerPlanner
from app.utils.report_composer_validator import ReportComposerValidator
from app.utils.report_field_registry import get_allowed_detail_fields
from app.utils.report_filter_builder import build_normalized_filters_from_plan
from app.utils.report_source_registry import get_allowed_sources
from app.utils.report_view_store import ReportViewStore, report_view_store


class ReportComposerService:
    def __init__(
        self,
        erpnext: ERPNextService | None = None,
        planner: ReportComposerPlanner | None = None,
        validator: ReportComposerValidator | None = None,
        engine: ReportAggregationEngine | None = None,
        store: ReportViewStore | None = None,
    ) -> None:
        self.erpnext = erpnext or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))
        self.planner = planner or ReportComposerPlanner()
        self.validator = validator or ReportComposerValidator()
        self.engine = engine or ReportAggregationEngine()
        self.store = store or report_view_store

    async def sources(self) -> dict[str, Any]:
        return get_allowed_sources()

    async def fields(self, source_name: str) -> dict[str, Any]:
        if source_name not in get_allowed_sources():
            raise AppError("This document type is not available for custom reports yet.", 422)
        return {"source_name": source_name, "fields": get_allowed_detail_fields(source_name)}

    async def plan_report(self, request: ReportComposerPlanRequest, cookies: dict | None = None) -> ReportComposerPlan:
        plan = await self.planner.plan_from_message(request.message, request.module_context)
        await self._audit("report_composer_plan_created", plan, "unknown", True)
        return plan

    async def run_report(self, request: ReportComposerRunRequest, cookies: dict | None = None, user: str = "unknown", conversation_id: str | None = None) -> ReportComposerResult:
        plan = self.validator.validate_plan(request.plan)
        if plan.missing_information:
            raise AppError(plan.warnings[0] if plan.warnings else "This report needs more information.", 422, {"missing_information": plan.missing_information})
        filters = build_normalized_filters_from_plan(plan)
        fields = self._required_source_fields(plan)
        result = await self.erpnext.list_records(plan.source.source_name, filters, fields, settings.report_composer_max_source_rows, cookies=cookies)
        permission = result.permissions.model_dump(mode="json")
        if not permission.get("allowed", True):
            await self._audit("report_composer_run_failed", plan, user, False, conversation_id, output=permission.get("reason"))
            raise PermissionDenied(permission.get("reason") or f"You do not have permission to read {plan.source.source_name}.")
        rows = self.engine.run(result.records, plan)
        chart = build_chart_from_report_result(rows, plan)
        columns = self._columns(rows)
        summary = self._summary(plan, rows)
        await self._audit("report_composer_run_completed", plan, user, True, conversation_id, row_count=len(rows))
        return ReportComposerResult(
            plan=plan,
            columns=columns,
            rows=rows,
            chart=chart,
            summary=summary,
            filters_applied=filters,
            source_metadata={"source_type": "doctype", "source_name": plan.source.source_name, "record_count": len(rows), "filters": filters},
            permission=permission,
        )

    async def save_view(self, request: SaveReportViewRequest, user: str, user_roles: list[str]) -> SavedReportView:
        if not settings.report_composer_save_views:
            raise AppError("Saved report views are disabled.", 403)
        request.plan = self.validator.validate_plan(request.plan)
        view = await self.store.save(request, user)
        await self._audit("report_composer_view_saved", request.plan, user, True, view_id=view.view_id)
        return view

    async def list_views(self, user: str, user_roles: list[str]) -> list[SavedReportView]:
        return await self.store.list(user, user_roles)

    async def get_view(self, view_id: str, user: str, user_roles: list[str]) -> SavedReportView:
        view = await self.store.get(view_id, user, user_roles)
        if not view:
            raise AppError("Saved report view was not found.", 404, {"view_id": view_id})
        return view

    async def delete_view(self, view_id: str, user: str, user_roles: list[str]) -> bool:
        deleted = await self.store.delete(view_id, user, user_roles)
        if deleted:
            await log_audit_event(AuditEvent(user=user, action="report_composer_view_deleted", agent_name="report_composer", allowed=True, risk_level="medium", input_summary=view_id, erp_data_sent=False))
        return deleted

    @staticmethod
    def _required_source_fields(plan: ReportComposerPlan) -> list[str]:
        fields = [field.fieldname for field in plan.fields]
        fields.extend(plan.group_by)
        fields.extend(metric.fieldname for metric in plan.metrics)
        for item in plan.filters:
            fields.append(item.fieldname)
        return list(dict.fromkeys(field for field in fields if field))

    @staticmethod
    def _columns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        return [{"key": key, "label": key.replace("_", " ").title(), "type": "number" if isinstance(next((row.get(key) for row in rows if row.get(key) is not None), None), (int, float)) else "text"} for key in keys]

    @staticmethod
    def _summary(plan: ReportComposerPlan, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return "No matching data found for this report."
        return f"I created {plan.title or 'a custom report'} with {len(rows)} row{'s' if len(rows) != 1 else ''}."

    @staticmethod
    async def _audit(action: str, plan: ReportComposerPlan, user: str, allowed: bool, conversation_id: str | None = None, row_count: int | None = None, output: str | None = None, view_id: str | None = None) -> None:
        await log_audit_event(AuditEvent(
            user=user or "unknown",
            conversation_id=conversation_id,
            action=action,
            agent_name="report_composer",
            tool_name="report_composer",
            doctype=plan.source.source_name,
            allowed=allowed,
            risk_level="medium" if action.endswith(("saved", "exported", "pinned_to_dashboard")) else "low",
            filters={item.fieldname: item.value for item in plan.filters},
            record_count=row_count,
            input_summary=f"group_by={plan.group_by}; metrics={[m.model_dump() for m in plan.metrics]}; chart={plan.chart.chart_type}",
            output_summary=output,
            widget_id=view_id,
            erp_data_sent=False,
        ))


report_composer_service = ReportComposerService()
