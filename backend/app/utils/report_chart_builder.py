from __future__ import annotations

from typing import Any

from app.schemas.report_composer import ReportComposerPlan


def build_chart_from_report_result(rows: list[dict[str, Any]], plan: ReportComposerPlan) -> dict[str, Any] | None:
    if not rows or plan.chart.chart_type == "none":
        return None
    x_key = plan.chart.x_key or (plan.group_by[0] if plan.group_by else next(iter(rows[0]), None))
    metric_key = plan.chart.y_key or plan.chart.value_key or _first_metric_key(rows[0], plan)
    if not x_key or not metric_key:
        return None
    chart_type = plan.chart.chart_type
    if chart_type in {"pie", "donut"}:
        return {
            "chart_type": chart_type,
            "title": plan.chart.title or plan.title or "Custom Report",
            "name_key": plan.chart.name_key or x_key,
            "value_key": metric_key,
            "data": rows,
        }
    return {
        "chart_type": chart_type,
        "title": plan.chart.title or plan.title or "Custom Report",
        "x_key": x_key,
        "y_key": metric_key,
        "series": [{"data_key": metric_key, "label": metric_key.replace("_", " ").title()}],
        "data": rows,
    }


def _first_metric_key(row: dict[str, Any], plan: ReportComposerPlan) -> str | None:
    for metric in plan.metrics:
        key = metric.output_key or f"{metric.fieldname}_{metric.function}"
        if key in row:
            return key
    for key, value in row.items():
        if isinstance(value, (int, float)) and key not in set(plan.group_by):
            return key
    return None
