from __future__ import annotations

import re
from typing import Any

from app.schemas.aggregation import AggregationMetric, AggregationPlan
from app.schemas.query_plan import QueryPlan
from app.utils.date_range_parser import parse_date_range_phrase
from app.utils.filter_normalizer import normalize_filters


AGGREGATION_CONFIG: dict[str, dict[str, Any]] = {
    "Sales Invoice": {"date_field": "posting_date", "groupable_fields": ["customer", "status", "territory", "currency"], "numeric_fields": ["grand_total", "outstanding_amount", "base_grand_total"], "default_metric": {"field": "grand_total", "function": "sum"}, "default_fields": ["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"]},
    "Purchase Invoice": {"date_field": "posting_date", "groupable_fields": ["supplier", "status", "currency"], "numeric_fields": ["grand_total", "outstanding_amount", "base_grand_total"], "default_metric": {"field": "grand_total", "function": "sum"}, "default_fields": ["name", "supplier", "posting_date", "grand_total", "outstanding_amount", "status"]},
    "Sales Order": {"date_field": "transaction_date", "groupable_fields": ["customer", "status", "currency"], "numeric_fields": ["grand_total", "base_grand_total"], "default_metric": {"field": "grand_total", "function": "sum"}, "default_fields": ["name", "customer", "transaction_date", "grand_total", "status"]},
    "Purchase Order": {"date_field": "transaction_date", "groupable_fields": ["supplier", "status", "currency"], "numeric_fields": ["grand_total", "base_grand_total"], "default_metric": {"field": "grand_total", "function": "sum"}, "default_fields": ["name", "supplier", "transaction_date", "grand_total", "status"]},
    "Quotation": {"date_field": "transaction_date", "groupable_fields": ["party_name", "status", "quotation_to", "currency"], "numeric_fields": ["grand_total", "base_grand_total"], "default_metric": {"field": "grand_total", "function": "sum"}, "default_fields": ["name", "quotation_to", "party_name", "transaction_date", "valid_till", "grand_total", "status"]},
    "Item": {"date_field": "creation", "groupable_fields": ["item_group", "stock_uom", "disabled"], "numeric_fields": [], "default_metric": {"field": "name", "function": "count"}, "default_fields": ["name", "item_code", "item_name", "item_group", "stock_uom", "disabled"]},
    "Customer": {"date_field": "creation", "groupable_fields": ["customer_group", "territory", "customer_type", "disabled"], "numeric_fields": [], "default_metric": {"field": "name", "function": "count"}, "default_fields": ["name", "customer_name", "customer_group", "territory"]},
    "Supplier": {"date_field": "creation", "groupable_fields": ["supplier_group", "country", "supplier_type", "disabled"], "numeric_fields": [], "default_metric": {"field": "name", "function": "count"}, "default_fields": ["name", "supplier_name", "supplier_group", "country"]},
}

AGGREGATION_INDICATORS = ("trend", "monthly", "daily", "yearly", "quarterly", " by ", "top ", "highest", "lowest", "total by", "sum by", "count by", "average by", "as chart", "as bar chart", "as pie chart", "as line chart")


def detect_aggregation_intent(message: str) -> bool:
    text = f" {' '.join(message.lower().split())} "
    return any(indicator in text for indicator in AGGREGATION_INDICATORS)


def build_rule_based_aggregation_plan(message: str, base_plan: QueryPlan) -> AggregationPlan | None:
    text = " ".join(message.lower().split())
    doctype = _resolve_aggregation_doctype(text, base_plan.doctype)
    if not doctype or doctype not in AGGREGATION_CONFIG or not detect_aggregation_intent(message):
        return None
    config = AGGREGATION_CONFIG[doctype]
    top_n = _top_n(text)
    group_by = _group_by(text, doctype)
    time_grain = _time_grain(text)
    time_field = config["date_field"] if time_grain else None
    metric = _metric(text, doctype)
    chart_type = _chart_type(text, bool(time_grain), bool(top_n or group_by))
    filters = dict(base_plan.normalized_filters or base_plan.filters or {})
    date_range = base_plan.date_range or parse_date_range_phrase(text)
    normalized_filters = normalize_filters(doctype, filters, date_range)
    normalized_filters = _drop_group_phrase_artifacts(text, normalized_filters)
    fields = _required_fields(config, group_by, metric, time_field)
    title = _title(message)
    plan = AggregationPlan(
        enabled=True,
        source_type="doctype",
        source_name=doctype,
        filters=normalized_filters,
        fields=fields,
        group_by=group_by,
        metrics=[AggregationMetric(**metric)],
        time_field=time_field,
        time_grain=time_grain,
        order_by_metric=_metric_key(metric),
        order_direction="asc" if "lowest" in text else "desc",
        limit=top_n or 20,
        chart_type=chart_type,
        chart_title=title,
        confidence=0.9,
        normalized_filters=normalized_filters,
    )
    return validate_aggregation_plan(plan)


def validate_aggregation_plan(plan: AggregationPlan) -> AggregationPlan:
    config = AGGREGATION_CONFIG.get(plan.source_name)
    if not config:
        raise ValueError(f"Unsupported aggregation source: {plan.source_name}")
    allowed_groups = set(config["groupable_fields"])
    for field in plan.group_by:
        if field not in allowed_groups:
            raise ValueError(f"Unsupported group_by field: {field}")
    allowed_metrics = set(config["numeric_fields"]) | {"name"}
    clean_metrics: list[AggregationMetric] = []
    for metric in plan.metrics:
        if metric.field not in allowed_metrics:
            raise ValueError(f"Unsupported metric field: {metric.field}")
        if metric.function != "count" and metric.field not in config["numeric_fields"]:
            raise ValueError(f"Metric {metric.function} requires a numeric field")
        clean_metrics.append(metric)
    plan.metrics = clean_metrics or [AggregationMetric(**config["default_metric"])]
    plan.limit = min(max(plan.limit, 1), 100)
    return plan


def _resolve_aggregation_doctype(text: str, fallback: str | None) -> str | None:
    if "purchase invoice" in text or "purchase invoices" in text:
        return "Purchase Invoice"
    if "purchase order" in text or "purchase orders" in text:
        return "Purchase Order"
    if "sales order" in text or "sales orders" in text:
        return "Sales Order"
    if "quotation" in text or "quotations" in text or "quote" in text:
        return "Quotation"
    if "item" in text or "items" in text or "stock balance" in text:
        return "Item"
    if "supplier" in text or "suppliers" in text:
        return "Supplier"
    if "customer" in text or "customers" in text:
        if "outstanding" in text or "sales" in text or "invoice" in text:
            return "Sales Invoice"
        return "Customer"
    if "purchase" in text:
        return "Purchase Invoice" if "invoice" in text else "Purchase Order"
    if "sales" in text or "invoice" in text or "unpaid" in text or "outstanding" in text:
        return "Sales Invoice"
    return fallback


def _group_by(text: str, doctype: str) -> list[str]:
    mapping = {
        "customer": {"Sales Invoice": "customer", "Sales Order": "customer", "Quotation": "party_name", "Customer": "customer_name"},
        "supplier": {"Purchase Invoice": "supplier", "Purchase Order": "supplier", "Supplier": "supplier_name"},
        "item group": {"Item": "item_group"},
        "status": {"Sales Invoice": "status", "Purchase Invoice": "status", "Sales Order": "status", "Purchase Order": "status", "Quotation": "status"},
        "territory": {"Customer": "territory", "Sales Invoice": "territory"},
        "country": {"Supplier": "country"},
    }
    for phrase, by_doctype in mapping.items():
        if f"by {phrase}" in text:
            field = by_doctype.get(doctype)
            return [field] if field else []
    if "top" in text and "customer" in text and doctype == "Sales Invoice":
        return ["customer"]
    if "top" in text and "supplier" in text and doctype == "Purchase Invoice":
        return ["supplier"]
    return []


def _metric(text: str, doctype: str) -> dict[str, str]:
    if "outstanding" in text or "unpaid" in text:
        return {"field": "outstanding_amount", "function": "sum", "label": "Outstanding"}
    if "average" in text or "avg" in text:
        return {"field": "grand_total", "function": "avg", "label": "Average"}
    if "count" in text or doctype in {"Item", "Customer", "Supplier"}:
        return {"field": "name", "function": "count", "label": "Count"}
    return dict(AGGREGATION_CONFIG[doctype]["default_metric"]) | {"label": "Total"}


def _time_grain(text: str) -> str | None:
    if "monthly" in text or " by month" in text or "value by month" in text:
        return "month"
    if "daily" in text or " by day" in text:
        return "day"
    if "quarter" in text:
        return "quarter"
    if "yearly" in text or " by year" in text:
        return "year"
    if "trend" in text:
        return "month"
    return None


def _chart_type(text: str, has_time: bool, has_group: bool) -> str:
    if "pie chart" in text:
        return "pie"
    if "donut" in text:
        return "donut"
    if "area" in text:
        return "area"
    if "line chart" in text or "trend" in text or has_time:
        return "line"
    if "bar chart" in text or has_group:
        return "bar"
    return "table"


def _top_n(text: str) -> int | None:
    match = re.search(r"\btop\s+(\d{1,3})\b", text)
    return min(int(match.group(1)), 100) if match else None


def _metric_key(metric: dict[str, str]) -> str:
    return f"{metric['field']}_{metric['function']}"


def _required_fields(config: dict[str, Any], group_by: list[str], metric: dict[str, str], time_field: str | None) -> list[str]:
    fields = list(dict.fromkeys([*group_by, metric["field"], time_field or "", *config["default_fields"]]))
    return [field for field in fields if field]


def _title(message: str) -> str:
    return " ".join(message.strip().split()).capitalize()


def _drop_group_phrase_artifacts(text: str, filters: dict[str, Any]) -> dict[str, Any]:
    output = dict(filters)
    if "by item group" in text and output.get("item_name") == ["like", "%group%"]:
        output.pop("item_name", None)
    return output
