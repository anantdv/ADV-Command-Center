from __future__ import annotations

import re

from app.config import settings
from app.core.exceptions import AppError
from app.schemas.report_composer import ReportComposerPlan, ReportMetric, ReportSelectedField
from app.utils.report_field_registry import (
    get_allowed_detail_fields,
    get_groupable_fields,
    get_numeric_fields,
    is_sensitive_field,
    resolve_field_alias,
    validate_fields,
    validate_group_by,
    validate_metrics,
)
from app.utils.report_source_registry import is_source_allowed


SQLISH = re.compile(r"\b(select|insert|update|delete|drop|alter|union|join|from\s+tab|;|--)\b", re.IGNORECASE)


class ReportComposerValidator:
    """Validates LLM/rule-produced report plans before any ERPNext data access."""

    def validate_plan(self, plan: ReportComposerPlan) -> ReportComposerPlan:
        source = plan.source.source_name
        if not is_source_allowed(source):
            raise AppError("This document type is not available for custom reports yet.", 422, {"source": source})
        self._reject_sql(plan.model_dump(mode="json"))

        plan.limit = min(max(plan.limit or settings.report_composer_default_limit, 1), settings.report_composer_default_limit)
        plan.fields = self._validate_selected_fields(plan)
        plan.group_by = validate_group_by(source, plan.group_by)
        plan.metrics = [ReportMetric(**metric) for metric in validate_metrics(source, [item.model_dump() for item in plan.metrics])]

        if plan.group_by and not plan.metrics:
            default = {"fieldname": "grand_total", "function": "sum", "label": "Total Amount"} if get_numeric_fields(source) else {"fieldname": "name", "function": "count", "label": "Count"}
            plan.metrics = [ReportMetric(**default)]

        if plan.output_mode in {"summary", "chart", "table_chart"} and not plan.group_by and not plan.metrics:
            plan.output_mode = "detail"
            plan.warnings.append("Chart/summary needs grouping or metrics, so I switched this to a detail table.")

        if plan.chart.chart_type != "none" and plan.output_mode == "detail":
            plan.output_mode = "table_chart" if plan.group_by else "detail"
            if not plan.group_by:
                plan.warnings.append("A chart needs a grouping field, so I returned a table for now.")

        allowed_groups = set(get_groupable_fields(source))
        for item in plan.filters:
            field = resolve_field_alias(source, item.fieldname)
            allowed = set(get_allowed_detail_fields(source)) | allowed_groups
            if field not in allowed or is_sensitive_field(field):
                raise AppError("One or more selected filters are not allowed for this report source.", 422, {"field": field})
            item.fieldname = field

        if not plan.fields and plan.output_mode == "detail":
            plan.fields = [ReportSelectedField(fieldname=field, label=field.replace("_", " ").title()) for field in get_allowed_detail_fields(source)[:8]]
        return plan

    @staticmethod
    def _validate_selected_fields(plan: ReportComposerPlan) -> list[ReportSelectedField]:
        source = plan.source.source_name
        valid = validate_fields(source, [field.fieldname for field in plan.fields])
        return [ReportSelectedField(fieldname=field, label=field.replace("_", " ").title()) for field in valid]

    def _reject_sql(self, value: object) -> None:
        if isinstance(value, dict):
            for nested in value.values():
                self._reject_sql(nested)
        elif isinstance(value, list):
            for nested in value:
                self._reject_sql(nested)
        elif isinstance(value, str) and SQLISH.search(value):
            raise AppError("This report request contains unsupported query-like text.", 422)
