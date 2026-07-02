from app.agents.router_agent import IntentResult
from app.schemas.chat import AssistantChatResponse, PermissionMeta, SourceMeta, SuggestedAction, TextPart, ToolCallPart
from app.tools.report_tools import ReportReadTools
from app.utils.chart_builder import try_build_chart
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.table_formatter import build_table_part


class ReportAgent:
    def __init__(self, tools: ReportReadTools | None = None):
        self.tools = tools or ReportReadTools()

    async def handle(self, intent: IntentResult, cookies: dict | None = None) -> AssistantChatResponse:
        if not intent.report_name:
            raise ValueError("ReportAgent requires an approved report name")
        result = await self.tools.run_report(intent.report_name, intent.filters, cookies)
        count = result["record_count"]
        summary = f"I ran {intent.report_name} and found {count} row{'s' if count != 1 else ''} you have permission to view."
        rows = result["rows"]
        parts = [
            TextPart(content=summary),
            ToolCallPart(
                tool_name="run_report",
                status="success",
                input_summary=intent.report_name,
                output_summary=f"{count} rows returned",
            ),
            build_table_part(intent.report_name, rows),
        ]
        chart = try_build_chart(intent.report_name, rows)
        if chart:
            parts.append(chart)
        message_id = new_id("msg")
        return AssistantChatResponse(
            conversation_id=intent.conversation_id or new_id("conv"),
            message_id=message_id,
            intent="run_report",
            parts=parts,
            source=SourceMeta.model_validate(result["source"]),
            permission=PermissionMeta.model_validate(result["permission"]),
            suggested_actions=[
                SuggestedAction(label="Generate PDF", action_type="generate_pdf"),
                SuggestedAction(label="Export Excel", action_type="export_excel"),
                SuggestedAction(label="Export CSV", action_type="export_csv"),
                SuggestedAction(label="Refine Filters", action_type="refine_filters"),
            ],
            id=message_id,
            content=summary,
            created_at=utc_now(),
        )
