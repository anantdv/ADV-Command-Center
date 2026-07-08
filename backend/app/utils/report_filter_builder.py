from __future__ import annotations

from typing import Any

from app.schemas.report_composer import ReportComposerPlan
from app.utils.filter_normalizer import normalize_filters
from app.utils.report_field_registry import resolve_field_alias
from app.utils.report_source_registry import get_default_date_field


def build_normalized_filters_from_plan(plan: ReportComposerPlan) -> dict[str, Any]:
    raw: dict[str, Any] = {}
    source = plan.source.source_name
    for item in plan.filters:
        field = resolve_field_alias(source, item.fieldname)
        raw[field] = item.value if item.operator == "=" else [item.operator, item.value]
    if plan.date_range and plan.date_range.get("from_date") and plan.date_range.get("to_date"):
        date_field = get_default_date_field(source)
        if date_field:
            raw[date_field] = ["between", [plan.date_range["from_date"], plan.date_range["to_date"]]]
    return normalize_filters(source, raw)
