from collections import Counter
from typing import Any

from app.schemas.chat import ChartPart
from app.utils.chart_data_normalizer import normalize_chart_data


def try_build_chart(title: str, rows: list[dict[str, Any]]) -> ChartPart | None:
    if not rows:
        return None
    keys = list(rows[0].keys())
    numeric_keys = [key for key in keys if any(_number(row.get(key)) is not None for row in rows)]
    date_keys = [key for key in keys if "date" in key or key.endswith("_on")]

    if date_keys and numeric_keys:
        date_key, numeric_key = date_keys[0], numeric_keys[0]
        data = [
            {date_key: row.get(date_key), numeric_key: _number(row.get(numeric_key))}
            for row in rows
            if row.get(date_key) is not None and _number(row.get(numeric_key)) is not None
        ]
        if data:
            return _chart_part(title=title, chart_type="line", data=data[:20], x_key=date_key, y_key=numeric_key)

    if "status" in keys:
        counts = Counter(str(row.get("status") or "Unknown") for row in rows)
        return _chart_part(
            title=f"{title} by Status",
            chart_type="bar",
            data=[{"status": status, "count": count} for status, count in counts.items()],
            x_key="status",
            y_key="count",
        )

    party_key = "customer" if "customer" in keys else "supplier" if "supplier" in keys else None
    if party_key and "grand_total" in keys:
        totals: dict[str, float] = {}
        for row in rows:
            party = str(row.get(party_key) or "Unknown")
            totals[party] = totals.get(party, 0) + (_number(row.get("grand_total")) or 0)
        data = [
            {party_key: party, "grand_total": total}
            for party, total in sorted(totals.items(), key=lambda item: item[1], reverse=True)[:10]
        ]
        return _chart_part(title=f"{title} by {party_key.title()}", chart_type="bar", data=data, x_key=party_key, y_key="grand_total")
    return None


def _chart_part(**kwargs: Any) -> ChartPart:
    return ChartPart.model_validate(normalize_chart_data(kwargs))


def infer_widget_chart_config(rows: list[dict[str, Any]], group_by: str | None = None, aggregate_field: str | None = None) -> dict[str, str]:
    """Infer only reusable chart keys; never copy source rows into widget metadata."""
    if not rows:
        return {"x_key": group_by or "category", "y_key": aggregate_field or "count"}
    keys = list(rows[0])
    x_key = group_by or next((key for key in ("status", "customer", "supplier", "item_group", "posting_date", "name") if key in keys), keys[0])
    y_key = aggregate_field or next((key for key in keys if key != x_key and any(_number(row.get(key)) is not None for row in rows)), "count")
    return {"x_key": x_key, "y_key": y_key}


def normalize_chart_widget_data(widget_type: str, rows: list[dict[str, Any]], chart_config: dict | None = None) -> dict[str, Any]:
    """Return the stable chart widget contract consumed by React/Recharts."""
    chart_type = {
        "bar_chart": "bar",
        "line_chart": "line",
        "pie_chart": "pie",
        "donut_chart": "donut",
        "area_chart": "area",
    }.get(widget_type, widget_type.replace("_chart", ""))
    data = list(rows or [])
    config = dict(chart_config or {})
    if chart_type in {"bar", "line", "area"}:
        config.setdefault("chart_type", chart_type)
        config.setdefault("x_key", "label")
        config.setdefault("y_key", "value")
        config.setdefault("series", [{"data_key": config["y_key"], "label": "Count"}])
    elif chart_type in {"pie", "donut"}:
        config.setdefault("chart_type", chart_type)
        config.setdefault("name_key", "label")
        config.setdefault("value_key", "value")
    else:
        config.setdefault("chart_type", chart_type or "bar")
    normalized = []
    for row in data:
        if "label" in row and "value" in row:
            normalized.append({"label": row.get("label"), "value": _number(row.get("value")) or 0})
            continue
        keys = list(row)
        preferred_label = config.get("x_key") or config.get("name_key")
        label_key = preferred_label if preferred_label in row else next((key for key in keys if _number(row.get(key)) is None), keys[0] if keys else "label")
        preferred_value = config.get("y_key") or config.get("value_key")
        value_key = preferred_value if preferred_value in row else next((key for key in keys if key != label_key and _number(row.get(key)) is not None), None)
        normalized.append({"label": str(row.get(label_key) or "Unknown"), "value": _number(row.get(value_key)) if value_key else 0})
    return {"data": normalized, "chart_config": config}


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
