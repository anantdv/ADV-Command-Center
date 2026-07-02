from app.agents.router_agent import IntentResult
from app.schemas.chat import (
    AssistantChatResponse,
    PermissionMeta,
    SourceMeta,
    SuggestedAction,
    TextPart,
    ToolCallPart,
)
from app.tools.erp_tools import ERPReadTools
from app.utils.chart_builder import try_build_chart
from app.utils.datetime import utc_now
from app.utils.ids import new_id
from app.utils.table_formatter import build_table_part


class ERPDataAgent:
    def __init__(self, tools: ERPReadTools | None = None):
        self.tools = tools or ERPReadTools()

    async def handle(self, intent: IntentResult, cookies: dict | None = None) -> AssistantChatResponse:
        conversation_id = intent.conversation_id or new_id("conv")
        if intent.intent == "write_blocked":
            summary = "Write operations are currently disabled in this read-only stage. I can still help you view records, analyze data, and prepare the action for review."
            return self._response(
                conversation_id,
                intent.intent,
                summary,
                [TextPart(content=summary)],
                suggested_actions=self._write_blocked_actions(),
            )

        if not intent.doctype:
            raise ValueError("ERPDataAgent requires a DocType intent")
        if intent.intent == "get_record" and intent.record_name:
            tool_name = "get_record"
            result = await self.tools.get_record(
                intent.doctype,
                intent.record_name,
                intent.fields,
                cookies,
            )
            summary = (
                f"I found {intent.doctype} {intent.record_name} and included the fields you have permission to view."
                if result["record_count"]
                else f"No permitted {intent.doctype} record was found for {intent.record_name}."
            )
            title = f"{intent.doctype} {intent.record_name}"
        else:
            tool_name = "list_records"
            result = await self.tools.list_records(
                intent.doctype,
                intent.filters,
                intent.fields,
                intent.limit,
                cookies=cookies,
            )
            count = result["record_count"]
            qualifier = "overdue " if (intent.filters or {}).get("status") == "Overdue" else ""
            summary = f"I found {count} {qualifier}{intent.doctype} record{'s' if count != 1 else ''} you have permission to view."
            title = intent.doctype

        rows = result["records"]
        parts = [
            TextPart(content=summary),
            ToolCallPart(
                tool_name=tool_name,
                status="success",
                input_summary=self._input_summary(intent),
                output_summary=f"{result['record_count']} records returned",
            ),
            build_table_part(title, rows),
        ]
        chart = try_build_chart(title, rows)
        if chart:
            parts.append(chart)
        return self._response(
            conversation_id,
            intent.intent,
            summary,
            parts,
            source=SourceMeta.model_validate(result["source"]),
            permission=PermissionMeta.model_validate(result["permission"]),
            suggested_actions=self._read_actions(),
        )

    @staticmethod
    def _response(
        conversation_id: str,
        intent: str,
        summary: str,
        parts: list,
        source: SourceMeta | None = None,
        permission: PermissionMeta | None = None,
        suggested_actions: list[SuggestedAction] | None = None,
    ) -> AssistantChatResponse:
        message_id = new_id("msg")
        return AssistantChatResponse(
            conversation_id=conversation_id,
            message_id=message_id,
            intent=intent,
            parts=parts,
            source=source,
            permission=permission,
            suggested_actions=suggested_actions or [],
            id=message_id,
            content=summary,
            created_at=utc_now(),
        )

    @staticmethod
    def _input_summary(intent: IntentResult) -> str:
        summary = intent.doctype or "ERP record"
        if intent.record_name:
            return f"{summary} {intent.record_name}"
        if intent.filters:
            return f"{summary} with approved filters"
        return summary

    @staticmethod
    def _read_actions() -> list[SuggestedAction]:
        return [
            SuggestedAction(label="Generate PDF", action_type="generate_pdf"),
            SuggestedAction(label="Export Excel", action_type="export_excel"),
            SuggestedAction(label="Export CSV", action_type="export_csv"),
            SuggestedAction(label="Refine Filters", action_type="refine_filters"),
        ]

    @staticmethod
    def _write_blocked_actions() -> list[SuggestedAction]:
        return [
            SuggestedAction(label="View related records", action_type="view_related"),
            SuggestedAction(label="Open module", action_type="open_module"),
            SuggestedAction(label="Prepare draft later", action_type="prepare_later", disabled=True, reason="Write workflows are not enabled."),
        ]
