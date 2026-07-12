from __future__ import annotations

import re
from datetime import datetime
from typing import Any


MONTH_FORMATS = ("%b %Y", "%B %Y", "%Y-%m-%d", "%Y-%m", "%Y")


def parse_period_label(value: Any) -> datetime | None:
    """Parse common report period labels without guessing from ERPNext data rows."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).strip()
    if not text:
        return None
    quarter = re.fullmatch(r"Q([1-4])\s+(\d{4})", text, flags=re.I)
    if quarter:
        month = (int(quarter.group(1)) - 1) * 3 + 1
        return datetime(int(quarter.group(2)), month, 1)
    for fmt in MONTH_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def sort_time_series_data(data: list[dict[str, Any]], x_key: str) -> list[dict[str, Any]]:
    """Sort parsed periods first and keep unparsable labels stable at the end."""
    indexed = list(enumerate(data or []))

    def key(item: tuple[int, dict[str, Any]]) -> tuple[int, datetime, int]:
        index, row = item
        parsed = parse_period_label(row.get(x_key))
        return (0, parsed, index) if parsed else (1, datetime.max, index)

    return [row for _, row in sorted(indexed, key=key)]


def normalize_chart_data(chart: dict[str, Any]) -> dict[str, Any]:
    """Normalize result chart data for stable UI actions and chart rendering."""
    normalized = dict(chart or {})
    data = list(normalized.get("data") or [])
    chart_type = str(normalized.get("chart_type") or "bar").lower()
    x_key = normalized.get("x_key") or normalized.get("name_key")
    y_key = normalized.get("y_key") or normalized.get("value_key")
    if not data or not x_key:
        normalized["data"] = data
        return normalized

    looks_temporal = any(parse_period_label(row.get(str(x_key))) for row in data)
    if looks_temporal and chart_type in {"line", "area", "bar"}:
        normalized["data"] = sort_time_series_data(data, str(x_key))
        return normalized

    if chart_type == "bar" and y_key:
        normalized["data"] = sorted(data, key=lambda row: _number(row.get(str(y_key))) or 0, reverse=True)
        return normalized

    normalized["data"] = data
    return normalized


def _number(value: Any) -> float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.replace("₹", "").replace(",", "").strip()
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None
