from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any

from app.schemas.aggregation import AggregationMetric, AggregationPlan


class AggregationEngine:
    def aggregate(self, rows: list[dict[str, Any]], plan: AggregationPlan) -> list[dict[str, Any]]:
        buckets: dict[tuple[Any, ...], dict[str, Any]] = {}
        states: dict[tuple[Any, ...], dict[str, list[float]]] = defaultdict(dict)
        for row in rows:
            key_values, label_fields = self._bucket_key(row, plan)
            key = tuple(key_values)
            bucket = buckets.setdefault(key, dict(label_fields))
            for metric in plan.metrics:
                metric_key = self._metric_key(metric)
                values = states[key].setdefault(metric_key, [])
                if metric.function == "count":
                    values.append(1)
                else:
                    number = _number(row.get(metric.field))
                    if number is not None:
                        values.append(number)
                bucket[metric_key] = self._compute(metric.function, values)

        output = list(buckets.values())
        if plan.order_by_metric:
            output.sort(key=lambda item: _number(item.get(plan.order_by_metric)) or 0, reverse=plan.order_direction == "desc")
        elif plan.time_grain:
            output.sort(key=lambda item: item.get("_period_sort") or "")
        for row in output:
            row.pop("_period_sort", None)
        return output[: plan.limit]

    def _bucket_key(self, row: dict[str, Any], plan: AggregationPlan) -> tuple[list[Any], dict[str, Any]]:
        values: list[Any] = []
        labels: dict[str, Any] = {}
        if plan.time_field and plan.time_grain:
            label, sort_key = _period(row.get(plan.time_field), plan.time_grain)
            values.append(sort_key)
            labels["period"] = label
            labels["_period_sort"] = sort_key
        for field in plan.group_by:
            value = row.get(field) or "Unknown"
            values.append(value)
            labels[field] = value
        if not values:
            values.append("All")
            labels["group"] = "All"
        return values, labels

    @staticmethod
    def _metric_key(metric: AggregationMetric) -> str:
        return f"{metric.field}_{metric.function}"

    @staticmethod
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


def _period(value: Any, grain: str) -> tuple[str, str]:
    parsed = _date(value)
    if not parsed:
        return "Unknown", "9999-99-99"
    if grain == "day":
        return parsed.isoformat(), parsed.isoformat()
    if grain == "week":
        year, week, _ = parsed.isocalendar()
        return f"W{week} {year}", f"{year}-W{week:02d}"
    if grain == "month":
        return parsed.strftime("%b %Y"), parsed.strftime("%Y-%m")
    if grain == "quarter":
        quarter = ((parsed.month - 1) // 3) + 1
        return f"Q{quarter} {parsed.year}", f"{parsed.year}-Q{quarter}"
    if grain == "year":
        return str(parsed.year), str(parsed.year)
    return parsed.isoformat(), parsed.isoformat()


def _date(value: Any) -> date | None:
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return date.fromisoformat(value[:10])
        except ValueError:
            return None
    return None
