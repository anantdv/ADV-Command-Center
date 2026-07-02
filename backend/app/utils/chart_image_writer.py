from io import BytesIO
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.core.exceptions import AppError


def write_chart_png(chart_config: dict[str, Any]) -> bytes:
    chart_type = str(chart_config.get("chart_type") or chart_config.get("type") or "bar").lower()
    data = chart_config.get("data") or []
    if not isinstance(data, list) or not data:
        raise AppError("Chart generation requires non-empty chart data.", 422)
    x_key = chart_config.get("x_key") or chart_config.get("xKey") or next(iter(data[0]), None)
    y_key = chart_config.get("y_key") or chart_config.get("yKey")
    if not y_key:
        y_key = next((key for key, value in data[0].items() if key != x_key and isinstance(value, (int, float))), None)
    if not x_key or not y_key:
        raise AppError("Chart data requires label and numeric value fields.", 422)
    labels = [str(item.get(x_key, "")) for item in data]
    values = [float(item.get(y_key) or 0) for item in data]
    colors = chart_config.get("colors")
    figure, axis = plt.subplots(figsize=(10, 5.6), constrained_layout=True)
    if chart_type == "line":
        axis.plot(labels, values, marker="o", color=(colors or [None])[0])
    elif chart_type == "area":
        axis.plot(labels, values, color=(colors or [None])[0])
        axis.fill_between(labels, values, alpha=.25, color=(colors or [None])[0])
    elif chart_type in {"pie", "donut"}:
        axis.pie(values, labels=labels, colors=colors, autopct="%1.1f%%", wedgeprops={"width": .45} if chart_type == "donut" else None)
    else:
        axis.bar(labels, values, color=colors)
    axis.set_title(str(chart_config.get("title") or "ADV Command Center Chart"))
    if chart_type not in {"pie", "donut"}:
        axis.set_xlabel(str(chart_config.get("x_label") or x_key.replace("_", " ").title()))
        axis.set_ylabel(str(chart_config.get("y_label") or y_key.replace("_", " ").title()))
        axis.tick_params(axis="x", rotation=30)
        axis.grid(axis="y", alpha=.2)
    stream = BytesIO()
    figure.savefig(stream, format="png", dpi=150, transparent=False)
    plt.close(figure)
    return stream.getvalue()
