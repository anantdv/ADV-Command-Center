from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PermissionMeta


class LibraryFileCreate(BaseModel):
    """Legacy create contract retained for older frontend callers."""

    name: str
    type: str
    module: str
    source_id: str | None = None


class LibraryFile(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    file_id: str
    file_name: str
    file_type: str
    file_format: str
    mime_type: str
    size_bytes: int | None = None
    source_module: str | None = None
    source_type: str | None = None
    source_name: str | None = None
    generated_by: str | None = None
    created_at: str
    permission_label: str = "Private"
    download_url: str | None = None
    permissions: PermissionMeta | None = None
    # Legacy fields consumed by the current Library cards.
    id: str
    name: str
    type: str
    module: str = "Cross-module"
    date: str
    permission: str = "Private"


class LibraryFileListResponse(BaseModel):
    files: list[LibraryFile] = Field(default_factory=list)


class DeleteResult(BaseModel):
    success: bool = True
