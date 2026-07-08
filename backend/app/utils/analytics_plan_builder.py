from __future__ import annotations

import re

from app.schemas.analytics import AnalyticsPlanResponse
from app.utils.analytics_catalog import ANALYTICS_CATALOG
from app.utils.date_range_parser import parse_date_range_phrase


class AnalyticsPlanBuilder:
    def build_from_prompt(self, message: str, query_plan: dict | None = None) -> AnalyticsPlanResponse:
        text = " ".join(message.lower().split())
        key = self._key(text)
        if not key:
            return AnalyticsPlanResponse(confidence=0.0)
        definition = ANALYTICS_CATALOG[key]
        return AnalyticsPlanResponse(
            analytics_key=key,
            title=definition["title"],
            confidence=0.92,
            date_range=parse_date_range_phrase(text),
            chart_type=_chart_type(text) or definition["default_chart"],
            limit=_top_n(text),
        )

    @staticmethod
    def _key(text: str) -> str | None:
        if "monthly sales trend" in text or ("sales trend" in text and "monthly" in text):
            return "monthly_sales_trend"
        if "top" in text and "customer" in text and "outstanding" in text:
            return "top_customers_by_outstanding"
        if "purchase order" in text and "supplier" in text:
            return "purchase_orders_by_supplier"
        if "sales order" in text and "status" in text:
            return "sales_orders_by_status"
        if "quotation" in text and "month" in text:
            return "quotation_value_by_month"
        if "customer" in text and "territory" in text:
            return "customers_by_territory"
        if "supplier" in text and "country" in text:
            return "suppliers_by_country"
        if "item" in text and "item group" in text:
            return "items_by_item_group"
        if "unpaid invoices by customer" in text:
            return "top_customers_by_outstanding"
        return None


def _top_n(text: str) -> int | None:
    match = re.search(r"\btop\s+(\d{1,3})\b", text)
    return int(match.group(1)) if match else None


def _chart_type(text: str) -> str | None:
    for chart in ("bar", "line", "pie", "donut", "area"):
        if f"{chart} chart" in text:
            return chart
    return None
