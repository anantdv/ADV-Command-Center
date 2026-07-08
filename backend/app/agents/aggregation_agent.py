from __future__ import annotations

from app.schemas.chat import AssistantChatResponse, ChartPart, PermissionMeta, SourceMeta, SuggestedAction, TextPart, ToolCallPart
from app.schemas.query_plan import QueryPlan
from app.services.aggregation_service import AggregationService
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.table_formatter import build_table_part


class AggregationAgent:
    def __init__(self, service: AggregationService | None = None):
        self.service = service or AggregationService()

    async def handle(self, plan: QueryPlan, cookies: dict | None = None, user: str = "unknown", conversation_id: str | None = None) -> AssistantChatResponse:
        if not plan.aggregation or not plan.aggregation.enabled:
            raise ValueError("AggregationAgent requires an enabled aggregation plan")
        conversation = conversation_id or new_id("conv")
        result = await self.service.run_aggregation(plan.aggregation, cookies, user, conversation)
        message_id = new_id("msg")
        parts = [
            TextPart(content=result.summary),
            ToolCallPart(tool_name="run_aggregation", status="success", input_summary=result.plan.source_name, output_summary=f"{len(result.rows)} grouped rows returned"),
            build_table_part(result.plan.chart_title or f"{result.plan.source_name} Summary", result.rows),
        ]
        if result.chart:
            parts.append(_chart_part(result.chart))
        source = SourceMeta(
            source_type="doctype",
            source_name=result.plan.source_name,
            record_count=len(result.rows),
            filters=result.source.get("filters") or {},
            doctype=result.plan.source_name,
            fields=result.plan.fields,
        )
        return AssistantChatResponse(
            conversation_id=conversation,
            message_id=message_id,
            intent="aggregation",
            parts=parts,
            source=source,
            permission=PermissionMeta.model_validate(result.permission or {"allowed": True, "risk_level": "low"}),
            suggested_actions=[
                SuggestedAction(label="Export Excel", action_type="export_excel"),
                SuggestedAction(label="Generate PDF", action_type="generate_pdf"),
                SuggestedAction(label="Pin to Overview", action_type="pin_to_overview"),
                SuggestedAction(label="Refine Filters", action_type="refine_filters"),
            ],
            id=message_id,
            content=result.summary,
            created_at=utc_now(),
        )


def _chart_part(chart: dict) -> ChartPart:
    chart_type = chart.get("chart_type") or "bar"
    x_key = chart.get("x_key") or chart.get("name_key")
    y_key = chart.get("y_key") or chart.get("value_key")
    if chart_type not in {"bar", "line", "pie", "donut", "area"}:
        chart_type = "bar"
    return ChartPart(title=chart.get("title") or "Aggregation Chart", chart_type=chart_type, data=chart.get("data") or [], x_key=x_key, y_key=y_key)
