from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError, PermissionDenied
from app.frappe.client import FrappeClient
from app.schemas.aggregation import AggregationPlan, AggregationResult
from app.services.erpnext_service import ERPNextService
from app.utils.aggregation_engine import AggregationEngine
from app.utils.aggregation_planner import validate_aggregation_plan
from app.utils.chart_plan_builder import build_chart_from_aggregation
from app.utils.filter_normalizer import normalize_filters


class AggregationService:
    def __init__(self, erpnext: ERPNextService | None = None, engine: AggregationEngine | None = None):
        self.erpnext = erpnext or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))
        self.engine = engine or AggregationEngine()

    async def run_aggregation(self, plan: AggregationPlan, cookies: dict | None = None, user: str = "unknown", conversation_id: str | None = None) -> AggregationResult:
        try:
            plan = validate_aggregation_plan(plan)
        except ValueError as exc:
            await self._audit("aggregation_plan_failed", plan, user, conversation_id, False, output=str(exc))
            raise AppError("I cannot safely aggregate by that field. Please choose a supported field for this document type.", 422, {"reason": str(exc)}) from exc

        filters = normalize_filters(plan.source_name, plan.filters or {})
        plan.normalized_filters = filters
        fields = self._required_fields(plan)
        result = await self.erpnext.list_records(plan.source_name, filters, fields, settings.aggregation_max_source_rows, cookies=cookies)
        permission = result.permissions.model_dump()
        if not permission.get("allowed", True):
            await self._audit("aggregation_permission_denied", plan, user, conversation_id, False)
            raise PermissionDenied(permission.get("reason") or f"You do not have permission to read {plan.source_name}.")

        rows = self.engine.aggregate(result.records, plan)
        if not rows:
            await self._audit("aggregation_empty_result", plan, user, conversation_id, True, row_count=0)
        chart = build_chart_from_aggregation(rows, plan)
        await self._audit("chart_plan_created", plan, user, conversation_id, True, row_count=len(rows))
        await self._audit("aggregation_executed", plan, user, conversation_id, True, row_count=len(rows))
        return AggregationResult(
            plan=plan,
            columns=self._columns(rows, plan),
            rows=rows,
            chart=chart,
            summary=self._summary(plan, rows),
            source={"source_type": "doctype", "source_name": plan.source_name, "filters": filters, "aggregation": plan.model_dump(mode="json")},
            permission=permission,
        )

    @staticmethod
    def _required_fields(plan: AggregationPlan) -> list[str]:
        fields = [*plan.fields, *plan.group_by]
        fields.extend(metric.field for metric in plan.metrics)
        if plan.time_field:
            fields.append(plan.time_field)
        return list(dict.fromkeys(field for field in fields if field))

    @staticmethod
    def _columns(rows: list[dict[str, Any]], plan: AggregationPlan) -> list[dict[str, Any]]:
        keys: list[str] = []
        for row in rows:
            for key in row:
                if key not in keys:
                    keys.append(key)
        if not keys:
            keys = ["period"] if plan.time_grain else (plan.group_by or ["group"])
        return [{"key": key, "label": key.replace("_", " ").title(), "type": "number" if key.endswith(("_sum", "_avg", "_min", "_max", "_count")) else "text"} for key in keys]

    @staticmethod
    def _summary(plan: AggregationPlan, rows: list[dict[str, Any]]) -> str:
        if not rows:
            return f"No matching data found for this {plan.source_name} summary."
        return f"I built a {plan.source_name} summary with {len(rows)} grouped row{'s' if len(rows) != 1 else ''}."

    @staticmethod
    async def _audit(action: str, plan: AggregationPlan, user: str, conversation_id: str | None, allowed: bool, row_count: int | None = None, output: str | None = None) -> None:
        await log_audit_event(AuditEvent(
            user=user,
            conversation_id=conversation_id,
            action=action,
            agent_name="aggregation_agent",
            tool_name="run_aggregation",
            doctype=plan.source_name if plan.source_type == "doctype" else None,
            report_name=plan.source_name if plan.source_type == "report" else None,
            allowed=allowed,
            risk_level="low",
            filters=plan.normalized_filters or plan.filters,
            record_count=row_count,
            input_summary=f"group_by={plan.group_by}; metrics={[m.model_dump() for m in plan.metrics]}; chart={plan.chart_type}",
            output_summary=output,
            erp_data_sent=False,
        ))


aggregation_service = AggregationService()
