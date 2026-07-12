from __future__ import annotations

import re
from typing import Any

from app.schemas.command_intent import CommandIntent
from app.utils.chart_intent_parser import detect_chart_request
from app.utils.context_isolation import has_explicit_context_reference, should_use_previous_context
from app.utils.report_alias_registry import resolve_report_alias


def detect_hard_intent(
    message: str,
    module_context: str | None = None,
    previous_context: dict | None = None,
) -> CommandIntent | None:
    text = " ".join(message.lower().split())
    explicit_context = has_explicit_context_reference(message)
    use_previous = bool(previous_context and should_use_previous_context(message))

    report = resolve_report_alias(text, module_context)
    if report:
        return CommandIntent(
            intent="run_report",
            source="hard_rule",
            confidence=0.99,
            message=message,
            module_context=report.get("module_context") or module_context,
            report_name=report["report_name"],
            explicit_context_reference=explicit_context,
            uses_previous_result=False,
        )

    chart = detect_chart_request(text)
    if chart and chart.get("analytics_key"):
        return CommandIntent(
            intent=chart["intent"],
            source="hard_rule",
            confidence=0.97,
            message=message,
            module_context=chart.get("module_context") or module_context,
            doctype=chart.get("doctype"),
            analytics_key=chart.get("analytics_key"),
            chart_requested=True,
            chart_type=chart.get("chart_type"),
            explicit_context_reference=explicit_context,
            uses_previous_result=False,
        )

    if re.search(r"\bshow unpaid invoices\b", text):
        return CommandIntent(
            intent="list_records",
            source="hard_rule",
            confidence=0.94,
            message=message,
            module_context=module_context or "Selling",
            doctype="Sales Invoice",
            filters={"status": ["in", ["Unpaid", "Overdue"]]},
            explicit_context_reference=explicit_context,
            uses_previous_result=False,
        )

    if use_previous:
        return None
    return None
