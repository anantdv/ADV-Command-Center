from __future__ import annotations

from collections import defaultdict
from typing import Any

from app.schemas.report_composer import ReportComposerPlan, ReportMetric


class ReportAggregationEngine:
    def run(self, rows: list[dict[str, Any]], plan: ReportComposerPlan) -> list[dict[str, Any]]:
        if plan.output_mode == "detail" or not plan.group_by:
            selected = [field.fieldname for field in plan.fields] or _keys(rows)
            return [{key: row.get(key) for key in selected if key in row} for row in rows[: plan.limit]]

        buckets: dict[tuple[Any, ...], dict[str, Any]] = {}
        states: dict[tuple[Any, ...], dict[str, list[float]]] = defaultdict(dict)
        for row in rows:
            key = tuple(row.get(field) or "Unknown" for field in plan.group_by)
            bucket = buckets.setdefault(key, {field: row.get(field) or "Unknown" for field in plan.group_by})
            for metric in plan.metrics:
                metric_key = metric.output_key or f"{metric.fieldname}_{metric.function}"
                values = states[key].setdefault(metric_key, [])
                if metric.function == "count":
                    values.append(1)
                else:
                    number = _number(row.get(metric.fieldname))
                    if number is not None:
                        values.append(number)
                bucket[metric_key] = _compute(metric.function, values)
        output = list(buckets.values())
        if plan.sort:
            sort = plan.sort[0]
            output.sort(key=lambda item: _number(item.get(sort.fieldname)) or 0, reverse=sort.direction == "desc")
        elif plan.metrics:
            metric_key = plan.metrics[0].output_key or f"{plan.metrics[0].fieldname}_{plan.metrics[0].function}"
            output.sort(key=lambda item: _number(item.get(metric_key)) or 0, reverse=True)
        return output[: plan.limit]


def _keys(rows: list[dict[str, Any]]) -> list[str]:
    keys: list[str] = []
    for row in rows:
        for key in row:
            if key not in keys:
                keys.append(key)
    return keys


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value.replace("₹", "").replace(",", "").strip())
        except ValueError:
            return None
    return None


def _compute(function: str, values: list[float]) -> float | int:
    if function == "count":
        return int(sum(values))
    if not values:
        return 0
    if function == "sum":
        return sum(values)
    if function == "avg":
        return sum(values) / len(values)
    if function == "min":
        return min(values)
    if function == "max":
        return max(values)
    return 0
