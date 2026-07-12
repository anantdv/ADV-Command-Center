from __future__ import annotations

import re
from typing import Any


def detect_chart_request(message: str) -> dict[str, Any] | None:
    text = " ".join(message.lower().split())
    explicit_chart = bool(re.search(r"\b(chart|graph|trend|visualize|line chart|bar chart|pie chart|donut chart)\b", text))

    chart_type = None
    if "pie" in text:
        chart_type = "pie"
    elif "donut" in text:
        chart_type = "donut"
    elif "bar" in text:
        chart_type = "bar"
    elif "line" in text or "trend" in text:
        chart_type = "line"

    mappings = [
        (r"\b(?:generate|show|create)?\s*(?:monthly\s+)?sales\s+(?:chart|trend|graph)|\bshow monthly sales\b", "monthly_sales_trend", "Sales Invoice", "Selling", chart_type or "line"),
        (r"\b(?:generate|show|create)?\s*purchase\s+(?:chart|trend|graph)|\bshow purchase trend\b", "monthly_purchase_trend", "Purchase Invoice", "Buying", chart_type or "line"),
        (r"\b(?:show\s+)?top customers\b|\bcustomer chart\b", "top_customers_by_sales", "Sales Invoice", "Selling", chart_type or "bar"),
        (r"\binvoice(?:s)?\s+(?:chart|by status)\b", "sales_invoices_by_status", "Sales Invoice", "Selling", chart_type or "pie"),
        (r"\bstock\s+(?:chart|by item group)\b", "stock_balance_by_item_group", "Item", "Stock", chart_type or "bar"),
        (r"\bitems?\s+by\s+item group\b", "items_by_item_group", "Item", "Stock", chart_type or "bar"),
        (r"\bpurchase orders? by supplier\b", "purchase_orders_by_supplier", "Purchase Order", "Buying", chart_type or "bar"),
    ]
    for pattern, analytics_key, doctype, module, default_chart in mappings:
        if re.search(pattern, text):
            force_chart = analytics_key in {"monthly_sales_trend", "monthly_purchase_trend"} or explicit_chart or "trend" in text
            return {
                "intent": "generate_chart" if force_chart else "run_analytics",
                "analytics_key": analytics_key,
                "doctype": doctype,
                "module_context": module,
                "chart_requested": True,
                "chart_type": default_chart,
            }
    if explicit_chart:
        return {"intent": "generate_chart", "chart_requested": True, "chart_type": chart_type or "bar"}
    return None
