import base64
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

import structlog

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError, PermissionDenied
from app.frappe.client import FrappeClient
from app.frappe.paths import REGISTER_GENERATED_FILE
from app.schemas.file_generation import GeneratedFileMeta, GenerateFileRequest, GenerateFileResponse
from app.services.erpnext_service import ERPNextService
from app.services.report_service import ReportService
from app.utils.chart_image_writer import write_chart_png
from app.utils.csv_writer import write_csv
from app.utils.excel_writer import write_excel
from app.utils.file_storage import FileStorage
from app.utils.pdf_writer import write_pdf_reportlab, write_pdf_weasyprint
from app.utils.report_renderer import render_html_report

logger = structlog.get_logger(__name__)
SENSITIVE_FIELD_PARTS = ("password", "secret", "token", "api_key", "api_secret", "otp", "bank_account", "account_no", "salary", "pan", "aadhaar")
FORMAT_DETAILS = {
    "xlsx": ("spreadsheet", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"),
    "csv": ("spreadsheet", "text/csv; charset=utf-8"),
    "pdf": ("pdf", "application/pdf"),
    "html": ("html_report", "text/html; charset=utf-8"),
    "png": ("chart", "image/png"),
}


class FileGenerationService:
    """Creates private artifacts only from permission-approved read results."""

    def __init__(self, client: FrappeClient | None = None, storage: FileStorage | None = None):
        self.client = client or FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name)
        self.erpnext = ERPNextService(self.client)
        self.reports = ReportService(self.client)
        self.storage = storage or FileStorage(settings.file_storage_root)

    async def generate_file(self, request: GenerateFileRequest, cookies: dict | None = None, generated_by: str = "unknown") -> GenerateFileResponse:
        if not settings.enable_file_generation:
            raise AppError("File generation is disabled.", 503)
        await self._audit("file_generation_requested", request, generated_by, allowed=True)
        try:
            rows, permission = await self._resolve_rows(request, cookies)
            if permission and not permission.get("allowed", True):
                raise PermissionDenied(permission.get("reason") or f"You do not have permission to export {request.source_name}.")
            if permission and permission.get("can_export") is False:
                raise PermissionDenied(f"You do not have export permission for {request.source_name}.")
            rows = self._safe_rows(rows)
            try:
                currency = (await self.erpnext.get_current_user_context(cookies)).company_currency
            except Exception:
                currency = "INR"
            warning = None
            if len(rows) > settings.max_export_rows:
                rows = rows[: settings.max_export_rows]
                warning = f"Export limited to first {settings.max_export_rows} rows."
            now = datetime.now(timezone.utc)
            title = request.title or request.source_name
            safe_stem = self._safe_stem(title)
            filename = f"{safe_stem}_{now.strftime('%Y-%m-%d_%H%M%S')}.{request.file_format}"
            file_id = f"file_{uuid4().hex[:16]}"
            metadata = {
                "file_id": file_id,
                "file_name": filename,
                "file_type": FORMAT_DETAILS[request.file_format][0],
                "file_format": request.file_format,
                "mime_type": FORMAT_DETAILS[request.file_format][1],
                "created_by": generated_by,
                "generated_by": generated_by,
                "created_at": now.isoformat(),
                "source_type": request.source_type,
                "source_name": request.source_name,
                "filters": request.filters or {},
                "conversation_id": request.conversation_id,
                "message_id": request.message_id,
                "row_count": len(rows),
                "warning": warning,
                "permission": permission or {"allowed": True, "risk_level": "medium"},
                "currency": currency,
            }
            content = self._render(request, title, rows, metadata)
            path = self.storage.save_bytes(file_id, filename, content)
            metadata["size_bytes"] = len(content)
            metadata["download_url"] = f"/api/library/files/{file_id}/download"
            self.storage.save_metadata(file_id, metadata)
            registered, registration_message = await self._register(metadata, cookies)
            await self._audit("file_generated", request, generated_by, True, file_id, filename, len(rows), len(content))
            return GenerateFileResponse(
                file=GeneratedFileMeta(
                    file_id=file_id, file_name=filename, file_type=metadata["file_type"], file_format=request.file_format,
                    mime_type=metadata["mime_type"], size_bytes=len(content), storage_path=path,
                    download_url=metadata["download_url"], generated_by=generated_by, source_type=request.source_type,
                    source_name=request.source_name, filters=request.filters or {}, created_at=now.isoformat(),
                ),
                registered_in_frappe=registered,
                registration_message=registration_message or warning,
            )
        except Exception as exc:
            await self._audit("file_generation_failed", request, generated_by, False, output=str(exc)[:180])
            raise

    async def _resolve_rows(self, request: GenerateFileRequest, cookies: dict | None) -> tuple[list[dict[str, Any]], dict[str, Any] | None]:
        if request.rows is not None:
            return request.rows, {"allowed": True, "risk_level": "medium", "confirmation_required": False}
        if request.source_type == "doctype":
            # TODO: Add a companion cursor/count API; its current safe list endpoint caps one request at 500 rows.
            result = await self.erpnext.list_records(request.source_name, request.filters or {}, request.fields, min(request.limit or settings.max_export_rows, settings.max_export_rows), cookies=cookies)
            return result.records, result.permissions.model_dump()
        if request.source_type == "report":
            result = await self.reports.run_report(request.source_name, request.filters or {}, cookies)
            return result.get("rows") or [], result.get("permission") or {"allowed": True, "risk_level": "medium"}
        raise AppError("chat_result generation requires supplied permission-approved rows.", 422)

    def _render(self, request: GenerateFileRequest, title: str, rows: list[dict[str, Any]], metadata: dict[str, Any]) -> bytes:
        writer_meta = {"source": f"{request.source_type}: {request.source_name}", "generated_by": metadata["generated_by"], "generated_at": metadata["created_at"], "filters": request.filters or {}, "currency": metadata.get("currency") or "INR"}
        if request.file_format == "xlsx": return write_excel(title, rows, writer_meta)
        if request.file_format == "csv": return write_csv(rows)
        if request.file_format == "html": return render_html_report(title, rows, writer_meta).encode("utf-8")
        if request.file_format == "png":
            chart = request.chart_config or self._chart_from_rows(title, rows)
            return write_chart_png(chart)
        html = render_html_report(title, rows[:500], writer_meta)
        if settings.pdf_renderer.lower() == "weasyprint":
            try: return write_pdf_weasyprint(html)
            except Exception as exc: logger.warning("weasyprint_fallback", error_type=type(exc).__name__)
        return write_pdf_reportlab(title, rows, writer_meta)

    async def _register(self, metadata: dict[str, Any], cookies: dict | None) -> tuple[bool, str | None]:
        if settings.use_mock_data:
            return False, "Mock mode: file stored locally and not registered in Frappe."
        payload = {
            "file_url": metadata["download_url"], "file_name": metadata["file_name"], "file_type": metadata["file_type"],
            "source_doctype": metadata["source_name"] if metadata["source_type"] == "doctype" else None,
            "source_report": metadata["source_name"] if metadata["source_type"] == "report" else None,
            "metadata": {"source_type": metadata["source_type"], "filters": metadata["filters"], "size_bytes": metadata["size_bytes"], "source_conversation": metadata.get("conversation_id"), "access_policy": "Private"},
        }
        try:
            await self.client.post(REGISTER_GENERATED_FILE, payload, cookies=cookies)
            await logger.ainfo("frappe_file_registered", file_id=metadata["file_id"], source=metadata["source_name"])
            return True, None
        except Exception as exc:
            logger.warning("frappe_file_registration_failed", file_id=metadata["file_id"], error_type=type(exc).__name__)
            return False, "File was generated locally, but Frappe registration failed."

    @staticmethod
    def _safe_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{key: value for key, value in row.items() if not any(term in key.lower() for term in SENSITIVE_FIELD_PARTS)} for row in rows]

    @staticmethod
    def _safe_stem(value: str) -> str:
        clean = re.sub(r"[^A-Za-z0-9_-]+", "_", value.strip()).strip("_")
        return (clean or "ERP_Report")[:100]

    @staticmethod
    def _chart_from_rows(title: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
        if not rows: raise AppError("No data is available for chart generation.", 422)
        keys = list(rows[0])
        x_key = next((key for key in keys if isinstance(rows[0].get(key), str)), keys[0])
        y_key = next((key for key in keys if isinstance(rows[0].get(key), (int, float)) and key != x_key), None)
        if not y_key: raise AppError("No numeric field is available for chart generation.", 422)
        return {"chart_type": "bar", "title": title, "data": rows[:20], "x_key": x_key, "y_key": y_key}

    async def _audit(self, action: str, request: GenerateFileRequest, user: str, allowed: bool, file_id: str | None = None, file_name: str | None = None, row_count: int | None = None, size_bytes: int | None = None, output: str | None = None) -> None:
        await log_audit_event(AuditEvent(user=user or "unknown", conversation_id=request.conversation_id, action=action, agent_name="file_generation_agent", tool_name=f"generate_{request.file_format}", doctype=request.source_name if request.source_type == "doctype" else None, report_name=request.source_name if request.source_type == "report" else None, allowed=allowed, risk_level="medium", input_summary=f"{request.source_type}:{request.source_name} -> {request.file_format}", output_summary=output or (f"{file_name}; {row_count or 0} rows; {size_bytes or 0} bytes" if file_id else None), filters=request.filters or {}, record_count=row_count, file_id=file_id, file_name=file_name, file_type=request.file_format, size_bytes=size_bytes, message_id=request.message_id))


file_generation_service = FileGenerationService()
