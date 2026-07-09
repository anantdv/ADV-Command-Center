from app.agents.router_agent import IntentResult
from app.schemas.chat import (
    AssistantChatResponse,
    PermissionMeta,
    RecordDetailPart,
    SourceMeta,
    SuggestedAction,
    TextPart,
    ToolCallPart,
)
from app.core.exceptions import AppError
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
            summary = intent.missing_info_hint or "I understood that you want an ERPNext record, but I need the document type to fetch it."
            return self._response(conversation_id, intent.intent, summary, [TextPart(content=summary)], permission=PermissionMeta(allowed=False, reason=summary))
        if intent.intent == "get_record" and intent.record_name:
            return await self.handle_document_detail(intent.doctype, intent.record_name, cookies, conversation_id)
        else:
            tool_name = "list_records"
            result = await self.tools.list_records(
                intent.doctype,
                intent.filters,
                intent.fields,
                intent.limit,
                cookies=cookies,
                date_range=intent.date_range,
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
            build_table_part(title, rows, doctype=intent.doctype),
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

    async def handle_document_detail(
        self,
        doctype: str,
        name: str,
        cookies: dict | None = None,
        conversation_id: str | None = None,
    ) -> AssistantChatResponse:
        conversation_id = conversation_id or new_id("conv")
        try:
            result = await self.tools.get_document_detail(doctype, name, cookies)
        except AppError as exc:
            summary = f"I understood that you want to open {doctype} {name}, but I could not fetch it from ERPNext."
            if exc.message:
                summary = f"{summary} {exc.message}"
            return self._response(
                conversation_id,
                "get_record",
                summary,
                [
                    TextPart(content=summary),
                    ToolCallPart(tool_name="get_document_detail", status="error", input_summary=f"{doctype} {name}", output_summary=exc.message),
                ],
                source=SourceMeta(source_type="doctype", source_name=doctype, record_count=0, filters={"name": name}, doctype=doctype),
                permission=PermissionMeta(allowed=False, reason=exc.message),
            )
        detail = result["detail"]
        summary = f"Here are the details for {doctype} {name}."
        parts = [
            TextPart(content=summary),
            ToolCallPart(tool_name="get_document_detail", status="success", input_summary=f"{doctype} {name}", output_summary="1 record returned"),
            RecordDetailPart(
                doctype=detail.get("doctype") or doctype,
                name=detail.get("name") or name,
                title=detail.get("title"),
                status=detail.get("status"),
                workflow_state=detail.get("workflow_state"),
                docstatus=detail.get("docstatus"),
                summary=detail.get("summary") or {},
                fields=detail.get("fields") or {},
                items=detail.get("items") or [],
                available_workflow_actions=detail.get("available_workflow_actions") or [],
            ),
        ]
        return self._response(
            conversation_id,
            "get_record",
            summary,
            parts,
            source=SourceMeta.model_validate(result["source"]),
            permission=PermissionMeta.model_validate(result["permission"]),
            suggested_actions=self._detail_actions(),
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
    def _detail_actions() -> list[SuggestedAction]:
        return [
            SuggestedAction(label="Show Related Records", action_type="view_related"),
            SuggestedAction(label="Open Module", action_type="open_module"),
        ]

    @staticmethod
    def _write_blocked_actions() -> list[SuggestedAction]:
        return [
            SuggestedAction(label="View related records", action_type="view_related"),
            SuggestedAction(label="Open module", action_type="open_module"),
            SuggestedAction(label="Prepare draft later", action_type="prepare_later", disabled=True, reason="Write workflows are not enabled."),
        ]
