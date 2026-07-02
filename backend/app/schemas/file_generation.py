from typing import Any, Literal

from pydantic import BaseModel, Field


class GenerateFileRequest(BaseModel):
    source_type: Literal["doctype", "report", "chat_result"]
    source_name: str = Field(min_length=1, max_length=140)
    file_format: Literal["xlsx", "csv", "pdf", "html", "png"]
    title: str | None = Field(default=None, max_length=180)
    filters: dict[str, Any] | None = None
    fields: list[str] | None = None
    rows: list[dict[str, Any]] | None = None
    chart_config: dict[str, Any] | None = None
    conversation_id: str | None = None
    message_id: str | None = None
    limit: int | None = Field(default=None, ge=1)


class GeneratedFileMeta(BaseModel):
    file_id: str
    file_name: str
    file_type: str
    file_format: str
    mime_type: str
    size_bytes: int
    storage_path: str = Field(exclude=True)
    download_url: str
    generated_by: str | None = None
    source_type: str
    source_name: str
    filters: dict[str, Any] | None = None
    created_at: str


class GenerateFileResponse(BaseModel):
    file: GeneratedFileMeta
    registered_in_frappe: bool = False
    registration_message: str | None = None
