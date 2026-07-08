from __future__ import annotations

from typing import Any

from app.schemas.chat import AssistantChatResponse, ChartPart, ConfirmationPart, FilePart, MissingFieldsPart, RecordPreviewPart, TablePart
from app.schemas.suggestions import SuggestionContext


class SuggestionContextBuilder:
    """Builds a row-free context object from an assistant response."""

    def from_assistant_result(
        self,
        assistant_response: AssistantChatResponse | dict[str, Any],
        query_plan: dict | None = None,
        tool_result: dict | None = None,
        previous_prompt: str | None = None,
        conversation_id: str | None = None,
        message_id: str | None = None,
    ) -> SuggestionContext:
        response = assistant_response if isinstance(assistant_response, AssistantChatResponse) else AssistantChatResponse.model_validate(assistant_response)
        parts = response.parts or []
        table = next((part for part in parts if isinstance(part, TablePart)), None)
        chart = next((part for part in parts if isinstance(part, ChartPart)), None)
        confirmation = next((part for part in parts if isinstance(part, ConfirmationPart)), None)
        record_preview = next((part for part in parts if isinstance(part, RecordPreviewPart)), None)
        missing = next((part for part in parts if isinstance(part, MissingFieldsPart)), None)
        file_part = next((part for part in parts if isinstance(part, FilePart)), None)

        result_type = self._result_type(response, table, chart, confirmation, record_preview, missing, file_part)
        columns = [column.key for column in table.columns] if table else []
        row_count = table.total_rows if table and table.total_rows is not None else (len(table.rows) if table else response.source.record_count if response.source else None)
        document_name = self._document_name(table, response)
        workflow_actions = self._workflow_actions(table, response)
        extra: dict[str, Any] = {}
        if confirmation:
            extra["confirmation_id"] = confirmation.confirmation_id
        if file_part:
            extra["download_url"] = file_part.download_url

        return SuggestionContext(
            conversation_id=conversation_id or response.conversation_id,
            message_id=message_id or response.message_id,
            previous_prompt=previous_prompt,
            result_type=result_type,
            doctype=(response.source.doctype if response.source else None) or (record_preview.doctype if record_preview else missing.doctype if missing else None),
            report_name=response.source.report_name if response.source else None,
            source_type=response.source.source_type if response.source else None,
            source_name=response.source.source_name if response.source else None,
            filters=response.source.filters if response.source and response.source.filters else {},
            fields=response.source.fields if response.source and response.source.fields else [],
            columns=columns,
            row_count=row_count,
            has_chart=chart is not None,
            chart_type=chart.chart_type if chart else None,
            document_name=document_name,
            workflow_actions=workflow_actions,
            available_actions=[action.action_type for action in response.suggested_actions],
            permissions=response.permission.model_dump(mode="json") if response.permission else {},
            extra=extra,
        )

    @staticmethod
    def _result_type(response: AssistantChatResponse, table: TablePart | None, chart: ChartPart | None, confirmation: ConfirmationPart | None, record_preview: RecordPreviewPart | None, missing: MissingFieldsPart | None, file_part: FilePart | None) -> str:
        if response.permission and not response.permission.allowed:
            return "error"
        if file_part:
            return "file_generated"
        if record_preview or missing or (confirmation and response.intent in {"crud_create", "crud_update"}):
            return "crud_preview"
        if response.intent == "workflow_list_pending":
            return "workflow_pending_list"
        if response.intent in {"workflow_get_detail", "workflow_apply_action"}:
            return "workflow_detail"
        if response.intent == "report_composer":
            return "report_composer"
        if response.intent == "aggregation":
            return "analytics"
        if table and (table.total_rows == 0 or len(table.rows) == 0):
            return "empty"
        if chart:
            return "chart"
        if table:
            return "table"
        return "unknown"

    @staticmethod
    def _document_name(table: TablePart | None, response: AssistantChatResponse) -> str | None:
        if response.source and response.source.filters:
            for key in ("name", "record_name"):
                if response.source.filters.get(key):
                    return str(response.source.filters[key])
        if not table or len(table.rows) != 1:
            return None
        row = table.rows[0]
        value = row.get("name") or row.get("customer") or row.get("supplier")
        return str(value) if value else None

    @staticmethod
    def _workflow_actions(table: TablePart | None, response: AssistantChatResponse) -> list[str]:
        if response.intent == "workflow_apply_action":
            action = (response.source.filters or {}).get("action") if response.source and response.source.filters else None
            return [str(action)] if action else []
        if not table:
            return []
        actions: list[str] = []
        for row in table.rows[:1]:
            raw = row.get("actions")
            if isinstance(raw, str):
                actions.extend(action.strip() for action in raw.split(",") if action.strip())
        return actions
