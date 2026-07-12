from __future__ import annotations

from typing import Any

from app.schemas.command_intent import CommandIntent
from app.utils.chart_intent_parser import detect_chart_request
from app.utils.context_isolation import has_explicit_context_reference, should_use_previous_context
from app.utils.date_range_parser import parse_date_range_phrase
from app.utils.detail_intent_parser import parse_detail_intent
from app.utils.hard_intent_detector import detect_hard_intent
from app.utils.report_alias_registry import resolve_report_alias
from app.utils.workflow_intent_parser import parse_workflow_intent


class CommandRouterService:
    async def route(
        self,
        message: str,
        module_context: str | None = None,
        date_range: dict | None = None,
        previous_context: dict | None = None,
        source: str = "chat",
    ) -> CommandIntent:
        text = " ".join(message.split())
        explicit_context = has_explicit_context_reference(text)
        use_previous = bool(previous_context and should_use_previous_context(text))
        prompt_date = parse_date_range_phrase(text)

        hard = detect_hard_intent(text, module_context, previous_context if use_previous else None)
        if hard:
            return self._with_context(hard, prompt_date or date_range, explicit_context, False)

        workflow = parse_workflow_intent(text)
        if workflow:
            return CommandIntent(
                intent=workflow["intent"],
                source="hard_rule",
                confidence=0.96,
                message=message,
                module_context=module_context,
                doctype=workflow.get("doctype"),
                record_name=workflow.get("record_name"),
                action_payload={"action": workflow.get("action")} if workflow.get("action") else {},
                explicit_context_reference=explicit_context,
                uses_previous_result=use_previous,
                date_range=prompt_date or date_range,
            )

        detail = parse_detail_intent(text)
        if detail.matched:
            return CommandIntent(
                intent="get_record_detail",
                source="hard_rule",
                confidence=detail.confidence,
                message=message,
                module_context=module_context,
                doctype=detail.doctype,
                record_name=detail.name,
                explicit_context_reference=explicit_context,
                uses_previous_result=use_previous,
                missing_information=["doctype"] if detail.needs_doctype else [],
            )

        report = resolve_report_alias(text, module_context)
        if report:
            return CommandIntent(intent="run_report", source="hard_rule", confidence=0.95, message=message, module_context=report.get("module_context") or module_context, report_name=report["report_name"], explicit_context_reference=explicit_context, date_range=prompt_date or date_range)

        chart = detect_chart_request(text)
        if chart and chart.get("analytics_key"):
            return CommandIntent(intent=chart["intent"], source="hard_rule", confidence=0.92, message=message, module_context=chart.get("module_context") or module_context, doctype=chart.get("doctype"), analytics_key=chart.get("analytics_key"), chart_requested=True, chart_type=chart.get("chart_type"), explicit_context_reference=explicit_context, date_range=prompt_date or date_range)

        return CommandIntent(intent="unsupported", source="fallback", confidence=0.0, message=message, module_context=module_context, explicit_context_reference=explicit_context, uses_previous_result=use_previous, date_range=prompt_date or date_range)

    @staticmethod
    def _with_context(intent: CommandIntent, date_range: dict[str, Any] | None, explicit_context: bool, uses_previous: bool) -> CommandIntent:
        intent.date_range = intent.date_range or date_range
        intent.explicit_context_reference = explicit_context
        intent.uses_previous_result = uses_previous
        return intent


command_router_service = CommandRouterService()
