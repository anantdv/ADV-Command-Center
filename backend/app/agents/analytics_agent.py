from __future__ import annotations

from app.agents.router_agent import IntentResult
from app.schemas.chat import AssistantChatResponse, ChartPart, PermissionMeta, SourceMeta, SuggestedAction, TextPart, ToolCallPart
from app.services.analytics_service import AnalyticsService, analytics_service
from app.utils.chart_data_normalizer import normalize_chart_data
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.table_formatter import build_table_part


class AnalyticsAgent:
    def __init__(self, service: AnalyticsService | None = None):
        self.service = service or analytics_service

    async def handle(self, intent: IntentResult, cookies: dict | None = None, user: str = "unknown") -> AssistantChatResponse:
        if not intent.analytics_key:
            raise ValueError("AnalyticsAgent requires an analytics key")
        chart_type = None
        if intent.chart_config:
            chart_type = str(intent.chart_config.get("chart_type") or "")
        result = await self.service.run_analytics(
            intent.analytics_key,
            intent.filters or {},
            intent.date_range,
            chart_type or None,
            intent.limit,
            cookies,
            user,
        )
        rows = result.rows
        chart = normalize_chart_data(result.chart or {})
        result_id = new_id("res")
        summary = result.summary or f"I generated {result.title}."
        parts = [
            TextPart(content=summary),
            ToolCallPart(tool_name="run_analytics", status="success", input_summary=result.title, output_summary=f"{len(rows)} rows returned"),
        ]
        if chart and chart.get("data"):
            parts.append(ChartPart(
                result_id=result_id,
                source_type="analytics",
                source_name=result.source.get("source_name") or intent.doctype or result.title,
                title=chart.get("title") or result.title,
                chart_type=_safe_chart_type(chart.get("chart_type") or chart_type or "bar"),
                data=chart.get("data") or [],
                x_key=chart.get("x_key") or chart.get("name_key") or "label",
                y_key=chart.get("y_key") or chart.get("value_key") or "value",
                config={"filters": result.filters, "date_range": intent.date_range, "analytics_key": intent.analytics_key},
                available_actions=["export_excel", "generate_pdf", "pin", "change_chart_type", "refine_filters", "change_columns", "save_report_view"],
            ))
        parts.append(build_table_part(result.title, rows, doctype=result.source.get("source_name")))
        message_id = new_id("msg")
        return AssistantChatResponse(
            conversation_id=intent.conversation_id or new_id("conv"),
            message_id=message_id,
            intent="generate_chart" if intent.intent == "generate_chart" else "run_analytics",
            parts=parts,
            source=SourceMeta(source_type="doctype", source_name=result.source.get("source_name") or intent.doctype or result.title, record_count=len(rows), filters=result.filters, doctype=result.source.get("source_name") or intent.doctype),
            permission=PermissionMeta.model_validate(result.permission or {"allowed": True, "risk_level": "low"}),
            suggested_actions=[
                SuggestedAction(label="Export Excel", action_type="export_excel"),
                SuggestedAction(label="Generate PDF", action_type="generate_pdf"),
                SuggestedAction(label="Pin to Overview", action_type="pin_to_overview"),
                SuggestedAction(label="Refine Filters", action_type="refine_filters"),
            ],
            id=message_id,
            content=summary,
            created_at=utc_now(),
        )


def _safe_chart_type(value: str) -> str:
    return value if value in {"bar", "line", "pie", "donut", "area"} else "bar"
