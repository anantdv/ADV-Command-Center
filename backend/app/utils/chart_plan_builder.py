from __future__ import annotations

from typing import Any

from app.schemas.aggregation import AggregationPlan


def build_chart_from_aggregation(result_rows: list[dict[str, Any]], plan: AggregationPlan) -> dict[str, Any] | None:
    if plan.chart_type == "table":
        return None
    metric = plan.metrics[0] if plan.metrics else None
    metric_key = plan.order_by_metric or (f"{metric.field}_{metric.function}" if metric else "value")
    title = plan.chart_title or f"{plan.source_name} Summary"
    if plan.chart_type in {"pie", "donut"}:
        name_key = "period" if plan.time_grain else (plan.group_by[0] if plan.group_by else "group")
        return {"chart_type": plan.chart_type, "title": title, "name_key": name_key, "value_key": metric_key, "data": result_rows}
    x_key = "period" if plan.time_grain else (plan.group_by[0] if plan.group_by else "group")
    return {
        "chart_type": plan.chart_type,
        "title": title,
        "x_key": x_key,
        "y_key": metric_key,
        "series": [{"data_key": metric_key, "label": metric.label or metric_key.replace("_", " ").title()}] if metric else [],
        "data": result_rows,
    }
