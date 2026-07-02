from app.agents.router_agent import IntentResult
from app.schemas.chat import AssistantChatResponse, FilePart, PermissionMeta, SourceMeta, SuggestedAction, TextPart, ToolCallPart
from app.tools.file_tools import FileGenerationTools
from app.utils.datetime import utc_now
from app.utils.ids import new_id


class FileGenerationAgent:
    def __init__(self, tools: FileGenerationTools | None = None):
        self.tools = tools or FileGenerationTools()

    async def handle(self, intent: IntentResult, cookies: dict | None = None, user: str = "unknown") -> AssistantChatResponse:
        if not intent.file_format or not intent.source_type or not intent.source_name:
            raise ValueError("FileGenerationAgent requires format and source metadata")
        method = {"xlsx": self.tools.generate_excel_from_source, "csv": self.tools.generate_csv_from_source, "pdf": self.tools.generate_pdf_from_source, "png": self.tools.generate_chart_image, "html": self.tools.save_html_report}[intent.file_format]
        generated = await method(source_type=intent.source_type, source_name=intent.source_name, title=intent.source_name, filters=intent.filters, fields=intent.fields, rows=intent.rows, chart_config=intent.chart_config, conversation_id=intent.conversation_id, cookies=cookies, user=user)
        file = generated.file
        summary = f"I generated {file.file_name} from the ERPNext data you have permission to view and saved it to your AI Library."
        file_part = FilePart(file_id=file.file_id, file_name=file.file_name, file_type=file.file_type, file_format=file.file_format, mime_type=file.mime_type, download_url=file.download_url, fileId=file.file_id, fileName=file.file_name, fileType=file.file_type, fileFormat=file.file_format, downloadUrl=file.download_url)
        message_id = new_id("msg")
        return AssistantChatResponse(conversation_id=intent.conversation_id or new_id("conv"), message_id=message_id, intent="generate_file", parts=[TextPart(content=summary), ToolCallPart(tool_name=f"generate_{file.file_format}", status="success", input_summary=f"{intent.source_type}: {intent.source_name}", output_summary=f"{file.file_name} ({file.size_bytes} bytes)"), file_part], source=SourceMeta(source_type=intent.source_type if intent.source_type != "chat_result" else "tool", source_name=intent.source_name, filters=intent.filters or {}), permission=PermissionMeta(allowed=True, risk_level="medium", confirmation_required=False), suggested_actions=[SuggestedAction(label="Download", action_type="download_file", reason=file.download_url), SuggestedAction(label="Open Library", action_type="open_library"), SuggestedAction(label="Generate another format", action_type="generate_another")], id=message_id, content=summary, created_at=utc_now())
