from __future__ import annotations

import re
from datetime import date

from app.config import settings
from app.schemas.report_composer import (
    ReportChartConfig,
    ReportComposerPlan,
    ReportFilter,
    ReportMetric,
    ReportSelectedField,
    ReportSource,
)
from app.utils.date_range_parser import parse_date_range_phrase
from app.utils.report_composer_validator import ReportComposerValidator
from app.utils.report_field_registry import resolve_field_alias
from app.utils.report_source_registry import get_default_date_field, resolve_source_from_text


class ReportComposerPlanner:
    """Builds safe custom-report plans from natural language.

    Gemini integration can be added here later, but this deterministic planner
    intentionally uses only the latest user prompt and allowlisted vocabulary.
    """

    def __init__(self, validator: ReportComposerValidator | None = None):
        self.validator = validator or ReportComposerValidator()

    async def plan_from_message(
        self,
        message: str,
        module_context: str | None = None,
        current_date: str | None = None,
    ) -> ReportComposerPlan:
        text = " ".join(message.lower().split())
        if self._is_multi_source(text):
            source = ReportSource(source_name="Sales Invoice")
            return ReportComposerPlan(
                title="Monthly sales and purchase comparison",
                source=source,
                output_mode="summary",
                missing_information=["multi_source_disabled"],
                warnings=["This report needs multiple sources. Multi-source report composition is not enabled yet."],
                confidence=0.85,
            )
        source_name = resolve_source_from_text(text) or "Sales Invoice"
        group_by = self._group_by(text, source_name)
        metrics = self._metrics(text, source_name)
        filters = self._filters(text, source_name)
        chart_type = self._chart_type(text, bool(group_by))
        date_range = parse_date_range_phrase(text, date.fromisoformat(current_date) if current_date else None)
        fields = self._fields(text, source_name)
        output_mode = "table_chart" if chart_type != "none" and (group_by or metrics) else ("summary" if group_by or metrics else "detail")
        title = self._title(message, source_name, group_by)
        plan = ReportComposerPlan(
            title=title,
            description=message.strip(),
            source=ReportSource(source_name=source_name),
            output_mode=output_mode,
            fields=[ReportSelectedField(fieldname=field, label=field.replace("_", " ").title()) for field in fields],
            filters=filters,
            group_by=group_by,
            metrics=metrics,
            limit=settings.report_composer_default_limit,
            chart=ReportChartConfig(chart_type=chart_type, title=title),
            date_range=date_range,
            confidence=0.9,
            view_name=self._view_name(message),
        )
        return self.validator.validate_plan(plan)

    @staticmethod
    def looks_like_report_prompt(message: str) -> bool:
        text = f" {' '.join(message.lower().split())} "
        indicators = (
            " create a report ", " make a report ", " build a report ", " custom report ",
            " save it as ", " save this report view ", " pin this report ", " sales and purchase comparison ",
        )
        return any(indicator in text for indicator in indicators)

    @staticmethod
    def _is_multi_source(text: str) -> bool:
        return "sales and purchase" in text or "purchase and sales" in text

    @staticmethod
    def _group_by(text: str, source_name: str) -> list[str]:
        if "customer-wise" in text or "customer wise" in text or "by customer" in text or "grouped by customer" in text:
            return ["customer"] if source_name in {"Sales Invoice", "Sales Order"} else ["party_name"] if source_name == "Quotation" else ["customer_group"]
        if "supplier-wise" in text or "supplier wise" in text or "by supplier" in text or "grouped by supplier" in text:
            return ["supplier"] if source_name in {"Purchase Invoice", "Purchase Order", "Purchase Receipt"} else ["supplier_group"]
        if "item group" in text:
            return ["item_group"]
        if "by status" in text or "grouped by status" in text:
            return ["status"]
        if "monthly" in text or "by month" in text:
            return []
        return []

    @staticmethod
    def _metrics(text: str, source_name: str) -> list[ReportMetric]:
        metrics: list[ReportMetric] = []
        if "count" in text or "number of" in text:
            label = "Invoice Count" if "invoice" in text else "Count"
            metrics.append(ReportMetric(fieldname="name", function="count", label=label))
        if any(term in text for term in ("total amount", "total value", "sales total", "purchase total", "value", "total")) and source_name not in {"Customer", "Supplier", "Item"}:
            metrics.append(ReportMetric(fieldname="grand_total", function="sum", label="Total Amount"))
        if "outstanding" in text or "unpaid" in text:
            metrics.append(ReportMetric(fieldname="outstanding_amount", function="sum", label="Outstanding Amount"))
        if not metrics:
            if source_name in {"Customer", "Supplier", "Item", "Issue", "Material Request"}:
                metrics.append(ReportMetric(fieldname="name", function="count", label="Count"))
            else:
                metrics.append(ReportMetric(fieldname="grand_total", function="sum", label="Total Amount"))
        return metrics

    @staticmethod
    def _filters(text: str, source_name: str) -> list[ReportFilter]:
        filters: list[ReportFilter] = []
        if source_name in {"Sales Invoice", "Purchase Invoice"}:
            if "overdue" in text:
                filters.append(ReportFilter(fieldname="status", operator="=", value="Overdue"))
            elif "unpaid" in text:
                filters.append(ReportFilter(fieldname="status", operator="in", value=["Unpaid", "Overdue"]))
            elif "paid" in text:
                filters.append(ReportFilter(fieldname="outstanding_amount", operator="=", value=0))
        if source_name == "Item" and "disabled" in text:
            filters.append(ReportFilter(fieldname="disabled", operator="=", value=1))
        if amount := re.search(r"\b(?:between|from)\s+([\d,]+(?:\.\d+)?)\s+(?:and|to|-)\s+([\d,]+(?:\.\d+)?)\b", text):
            field = "grand_total" if source_name not in {"Item", "Customer", "Supplier"} else "name"
            if field != "name":
                filters.append(ReportFilter(fieldname=field, operator="between", value=[_num(amount.group(1)), _num(amount.group(2))]))
        return filters

    @staticmethod
    def _chart_type(text: str, has_group: bool) -> str:
        if "pie" in text:
            return "pie"
        if "donut" in text:
            return "donut"
        if "line" in text or "trend" in text or "monthly" in text:
            return "line"
        if "area" in text:
            return "area"
        if "chart" in text or has_group:
            return "bar"
        return "none"

    @staticmethod
    def _fields(text: str, source_name: str) -> list[str]:
        match = re.search(r"\bwith\s+(.+?)(?:\s+for\s+|\s+and save|\s+as\s+\w+\s+chart|$)", text)
        if not match:
            return []
        pieces = [piece.strip(" .") for piece in re.split(r",|\band\b", match.group(1)) if piece.strip()]
        return [resolve_field_alias(source_name, piece) for piece in pieces if piece]

    @staticmethod
    def _title(message: str, source_name: str, group_by: list[str]) -> str:
        saved = ReportComposerPlanner._view_name(message)
        if saved:
            return saved
        if group_by:
            return f"{source_name} by {', '.join(field.replace('_', ' ').title() for field in group_by)}"
        return f"{source_name} Custom Report"

    @staticmethod
    def _view_name(message: str) -> str | None:
        match = re.search(r"\bsave (?:it|this report)?\s*(?:as|named)\s+(.+)$", message, re.IGNORECASE)
        if match:
            return match.group(1).strip(" .\"'")
        return None


def _num(value: str) -> float:
    return float(value.replace(",", ""))
