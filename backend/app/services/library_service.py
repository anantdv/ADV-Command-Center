import re
from datetime import date
from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import PermissionDenied
from app.db.seed import FULL_PERMISSION
from app.frappe.client import FrappeClient
from app.frappe.paths import LIST_GENERATED_FILES
from app.schemas.common import PermissionMeta
from app.schemas.library import DeleteResult, LibraryFile, LibraryFileCreate
from app.utils.file_storage import FileStorage


class LibraryService:
    def __init__(self, client: FrappeClient | None = None, storage: FileStorage | None = None) -> None:
        self.client = client or FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name)
        self.storage = storage or FileStorage(settings.file_storage_root)
        self.legacy_files = self._legacy_files()

    async def list_files(self, file_type: str | None = None, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> list[LibraryFile]:
        local = [self._from_metadata(item) for item in self.storage.list_metadata() if self._can_access(item, user, roles)]
        if settings.use_mock_data:
            result = [*local, *self.legacy_files]
        else:
            remote = await self._list_frappe(file_type, cookies)
            local_ids = {item.file_id for item in local}
            result = [*local, *(item for item in remote if item.file_id not in local_ids)]
        return [item for item in result if not file_type or self._matches_type(item, file_type)]

    async def get_file_metadata(self, file_id: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> LibraryFile:
        metadata = self.storage.read_metadata(file_id)
        if not self._can_access(metadata, user, roles):
            raise PermissionDenied("You do not have permission to access this generated file.")
        return self._from_metadata(metadata)

    async def download_file(self, file_id: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> tuple[bytes, str, str]:
        file = await self.get_file_metadata(file_id, cookies, user, roles)
        content = self.storage.read_bytes(file_id)
        await log_audit_event(AuditEvent(user=user, action="file_downloaded", tool_name="download_file", allowed=True, risk_level="medium", input_summary=file_id, output_summary=f"{file.file_name}; {len(content)} bytes", file_id=file_id, file_name=file.file_name, file_type=file.file_format, size_bytes=len(content)))
        return content, file.mime_type, file.file_name

    async def delete_file(self, file_id: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> DeleteResult:
        file = await self.get_file_metadata(file_id, cookies, user, roles)
        self.storage.delete(file_id)
        await log_audit_event(AuditEvent(user=user, action="file_deleted", tool_name="delete_file", allowed=True, risk_level="medium", input_summary=file_id, output_summary=file.file_name, file_id=file_id, file_name=file.file_name, file_type=file.file_format))
        return DeleteResult()

    async def create_file(self, request: LibraryFileCreate) -> LibraryFile:
        # Legacy metadata-only endpoint behavior is retained for old callers.
        return LibraryFile(file_id=f"legacy_{len(self.legacy_files)+1}", file_name=request.name, file_type=request.type, file_format=request.name.rsplit(".", 1)[-1].lower(), mime_type="application/octet-stream", source_module=request.module, generated_by="Admin User + AI", created_at=date.today().isoformat(), id=f"legacy_{len(self.legacy_files)+1}", name=request.name, type=request.type, module=request.module, date=date.today().isoformat(), permission="Private", permissions=PermissionMeta(**FULL_PERMISSION))

    async def _list_frappe(self, file_type: str | None, cookies: dict | None) -> list[LibraryFile]:
        payload = await self.client.get(LIST_GENERATED_FILES, {"file_type": file_type} if file_type else None, cookies)
        companion = payload.get("message", payload)
        rows = companion.get("data", []) if isinstance(companion, dict) and "success" in companion else companion
        return [self._from_frappe(row) for row in (rows or [])]

    @staticmethod
    def _can_access(metadata: dict[str, Any], user: str, roles: list[str] | None) -> bool:
        return settings.use_mock_data or metadata.get("generated_by") in {None, "", "unknown", user} or bool(set(roles or []).intersection({"System Manager", "AI Command Center Manager"}))

    @staticmethod
    def _matches_type(item: LibraryFile, requested: str) -> bool:
        aliases = {"spreadsheets": "spreadsheet", "pdf": "pdf", "charts": "chart", "dashboards": "dashboard"}
        return item.file_type.lower() == aliases.get(requested.lower(), requested.lower()) or item.type.lower() == requested.lower()

    @staticmethod
    def _from_metadata(data: dict[str, Any]) -> LibraryFile:
        file_type = str(data.get("file_type") or "file")
        created = str(data.get("created_at") or "")
        return LibraryFile(file_id=data["file_id"], file_name=data["file_name"], file_type=file_type, file_format=str(data.get("file_format") or ""), mime_type=str(data.get("mime_type") or "application/octet-stream"), size_bytes=data.get("size_bytes"), source_type=data.get("source_type"), source_name=data.get("source_name"), generated_by=data.get("generated_by") or data.get("created_by"), created_at=created, download_url=data.get("download_url"), id=data["file_id"], name=data["file_name"], type=LibraryService._display_type(file_type), module=data.get("source_name") or "Cross-module", date=created[:10], permission="Private", permissions=PermissionMeta(**FULL_PERMISSION))

    @staticmethod
    def _from_frappe(data: dict[str, Any]) -> LibraryFile:
        url = data.get("file_url") or ""
        match = re.search(r"/files/(file_[A-Za-z0-9]+)/download", url)
        file_id = match.group(1) if match else str(data.get("name"))
        file_type = str(data.get("file_type") or "file")
        name = str(data.get("file_title") or data.get("name"))
        fmt = name.rsplit(".", 1)[-1].lower() if "." in name else ""
        return LibraryFile(file_id=file_id, file_name=name, file_type=file_type, file_format=fmt, mime_type="application/octet-stream", source_type="report" if data.get("source_report") else "doctype", source_name=data.get("source_report") or data.get("source_doctype"), generated_by=data.get("generated_by"), created_at=str(data.get("creation") or ""), download_url=url or None, id=file_id, name=name, type=LibraryService._display_type(file_type), module=data.get("source_report") or data.get("source_doctype") or "Cross-module", date=str(data.get("creation") or "")[:10], permission=data.get("access_policy") or "Private", permissions=PermissionMeta(can_read=True, allowed=True))

    @staticmethod
    def _display_type(value: str) -> str:
        return {"spreadsheet": "Spreadsheet", "pdf": "PDF Report", "chart": "Chart", "html_report": "HTML Report"}.get(value.lower(), value.title())

    @staticmethod
    def _legacy_files() -> list[LibraryFile]:
        permission = PermissionMeta(**FULL_PERMISSION)
        rows = [
            ("Monthly Sales Report.xlsx", "spreadsheet", "Spreadsheet", "Selling"),
            ("Receivable Aging.pdf", "pdf", "PDF Report", "Accounting"),
            ("Top Customers Chart.png", "chart", "Chart", "Selling"),
            ("CEO Overview Dashboard", "dashboard", "Dashboard", "Cross-module"),
            ("Stock Movement Analysis.xlsx", "spreadsheet", "Spreadsheet", "Stock"),
        ]
        return [LibraryFile(file_id=f"file-legacy-{index}", file_name=name, file_type=file_type, file_format=name.rsplit(".", 1)[-1] if "." in name else "dashboard", mime_type="application/octet-stream", generated_by="Tinni", created_at="2026-07-01", id=f"file-{index:03d}", name=name, type=display_type, module=module, date="2026-07-01", permission="Private", permissions=permission) for index, (name, file_type, display_type, module) in enumerate(rows, 1)]


library_service = LibraryService()
