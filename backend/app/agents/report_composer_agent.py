from __future__ import annotations

from app.agents.router_agent import IntentResult
from app.schemas.chat import AssistantChatResponse, ChartPart, PermissionMeta, SourceMeta, SuggestedAction, TableColumn, TablePart, TextPart, ToolCallPart
from app.schemas.report_composer import ReportComposerPlanRequest, ReportComposerRunRequest, SaveReportViewRequest
from app.services.report_composer_service import ReportComposerService, report_composer_service
from app.utils.chart_data_normalizer import normalize_chart_data
from app.utils.datetime import utc_now
from app.utils.ids import new_id


class ReportComposerAgent:
    def __init__(self, service: ReportComposerService | None = None):
        self.service = service or report_composer_service

    async def handle(self, intent: IntentResult, cookies: dict | None = None, user: str = "unknown") -> AssistantChatResponse:
        conversation_id = intent.conversation_id or new_id("conv")
        message_id = new_id("msg")
        plan = intent.report_composer_plan
        if plan is None:
            plan = await self.service.plan_report(ReportComposerPlanRequest(message=intent.raw_prompt), cookies)
        if plan.missing_information:
            summary = plan.warnings[0] if plan.warnings else "This report needs more information before I can run it."
            return AssistantChatResponse(
                conversation_id=conversation_id,
                message_id=message_id,
                intent="report_composer",
                parts=[TextPart(content=summary), ToolCallPart(tool_name="report_composer_plan", status="error", input_summary=intent.raw_prompt, output_summary=summary)],
                permission=PermissionMeta(allowed=False, risk_level="low", reason=summary),
                suggested_actions=[SuggestedAction(label="Try a single-source report", action_type="prompt", reason="Example: sales invoices by customer for 2025")],
                id=message_id,
                content=summary,
                created_at=utc_now(),
            )
        result = await self.service.run_report(ReportComposerRunRequest(plan=plan), cookies, user, conversation_id)
        parts = [
            TextPart(content=result.summary),
            ToolCallPart(tool_name="report_composer_run", status="success", input_summary=plan.title or plan.source.source_name, output_summary=f"{len(result.rows)} rows returned"),
            TablePart(title=plan.title or plan.source.source_name, columns=[TableColumn(**column) for column in result.columns], rows=result.rows, total_rows=len(result.rows)),
        ]
        if result.chart:
            chart = normalize_chart_data(result.chart)
            chart_type = chart.get("chart_type", "bar")
            if chart_type not in {"bar", "line", "pie", "donut", "area"}:
                chart_type = "bar"
            parts.append(ChartPart(result_id=new_id("res"), source_type="report_composer", source_name=plan.source.source_name, title=chart.get("title") or plan.title or "Custom Report", chart_type=chart_type, data=chart.get("data", result.rows), x_key=chart.get("x_key") or chart.get("name_key"), y_key=chart.get("y_key") or chart.get("value_key"), config={"filters": result.filters_applied, "plan": plan.model_dump(mode="json")}, available_actions=["export_excel", "generate_pdf", "pin", "change_chart_type", "refine_filters", "change_columns", "save_report_view"]))
        saved_summary = None
        if plan.view_name:
            view = await self.service.save_view(SaveReportViewRequest(name=plan.view_name, plan=plan), user, [])
            saved_summary = f"Saved view {view.name}."
            parts.append(ToolCallPart(tool_name="save_report_view", status="success", input_summary=plan.view_name, output_summary=f"View {view.view_id} saved"))
        if saved_summary:
            parts.insert(1, TextPart(content=saved_summary))
        permission = PermissionMeta(**(result.permission or {"allowed": True, "risk_level": "low"}))
        source = SourceMeta(source_type="tool", source_name="Report Composer", record_count=len(result.rows), filters=result.filters_applied, doctype=plan.source.source_name, fields=[field.fieldname for field in plan.fields])
        suggested = [
            SuggestedAction(label="Save View", action_type="save_report_view"),
            SuggestedAction(label="Export Excel", action_type="export_excel"),
            SuggestedAction(label="Pin to Overview", action_type="pin_to_overview"),
            SuggestedAction(label="Change Chart", action_type="change_chart"),
        ]
        content = " ".join(part.content for part in parts if isinstance(part, TextPart))
        return AssistantChatResponse(conversation_id=conversation_id, message_id=message_id, intent="report_composer", parts=parts, source=source, permission=permission, suggested_actions=suggested, id=message_id, content=content, created_at=utc_now())
