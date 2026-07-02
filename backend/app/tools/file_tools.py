from typing import Any

from app.schemas.file_generation import GenerateFileRequest, GenerateFileResponse
from app.services.file_generation_service import FileGenerationService, file_generation_service


class FileGenerationTools:
    def __init__(self, service: FileGenerationService | None = None):
        self.service = service or file_generation_service

    async def _generate(self, file_format: str, source_type: str, source_name: str, *, title: str | None = None, filters: dict | None = None, fields: list[str] | None = None, rows: list[dict[str, Any]] | None = None, chart_config: dict[str, Any] | None = None, conversation_id: str | None = None, message_id: str | None = None, cookies: dict | None = None, user: str = "unknown") -> GenerateFileResponse:
        return await self.service.generate_file(GenerateFileRequest(source_type=source_type, source_name=source_name, file_format=file_format, title=title, filters=filters, fields=fields, rows=rows, chart_config=chart_config, conversation_id=conversation_id, message_id=message_id), cookies, user)

    async def generate_excel_from_source(self, **kwargs) -> GenerateFileResponse: return await self._generate("xlsx", **kwargs)
    async def generate_csv_from_source(self, **kwargs) -> GenerateFileResponse: return await self._generate("csv", **kwargs)
    async def generate_pdf_from_source(self, **kwargs) -> GenerateFileResponse: return await self._generate("pdf", **kwargs)
    async def generate_chart_image(self, **kwargs) -> GenerateFileResponse: return await self._generate("png", **kwargs)
    async def save_html_report(self, **kwargs) -> GenerateFileResponse: return await self._generate("html", **kwargs)


FILE_TOOL_NAMES = ["generate_excel", "generate_csv", "generate_pdf", "generate_chart_png", "generate_html_report", "save_to_library"]
