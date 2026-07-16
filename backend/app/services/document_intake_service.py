from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import UploadFile

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError
from app.schemas.document_intake import DocumentMappingPreview, DocumentUploadResponse, ExtractedDocumentFields, OCRResult, UpdateMappingPreviewRequest
from app.services.crud_service import crud_service
from app.services.document_mapping_service import DocumentMappingService
from app.services.ocr_service import OCRService
from app.utils.file_type_validator import validate_upload
from app.utils.ids import new_id
from app.utils.ocr_field_extractor import extract_document_fields


class DocumentIntakeService:
    def __init__(self) -> None:
        self.root = Path(settings.document_intake_storage_root)
        self.ocr = OCRService()
        self.mapper = DocumentMappingService()
        self.max_file_size_mb = settings.ocr_max_file_size_mb

    async def upload(self, file: UploadFile, user: str = "unknown") -> DocumentUploadResponse:
        content = await file.read()
        validate_upload(file.filename or "upload", file.content_type, len(content), settings.ocr_max_file_size_mb)
        await log_audit_event(AuditEvent(user=user, action="document_upload_started", tool_name="document_intake", allowed=True, risk_level="medium", input_summary=file.filename or "upload", output_summary=f"{len(content)} bytes", file_name=file.filename or "upload"))
        intake_id = new_id("intake")
        directory = self.root / intake_id
        directory.mkdir(parents=True, exist_ok=True)
        safe_name = Path(file.filename or "document").name
        path = directory / safe_name
        path.write_bytes(content)
        meta = {"intake_id": intake_id, "file_id": intake_id, "file_name": safe_name, "mime_type": file.content_type or "application/octet-stream", "status": "uploaded", "path": str(path), "user": user}
        self._write_meta(intake_id, meta)
        await log_audit_event(AuditEvent(user=user, action="document_intake_uploaded", tool_name="document_intake", allowed=True, risk_level="medium", input_summary=safe_name, output_summary=intake_id, file_id=intake_id, file_name=safe_name))
        return DocumentUploadResponse(intake_id=intake_id, file_id=intake_id, file_name=safe_name, mime_type=meta["mime_type"], status="uploaded", message="Document uploaded. Process OCR to continue.")

    async def process(self, intake_id: str, cookies: dict | None = None, user: str = "unknown") -> DocumentMappingPreview:
        meta = self._meta(intake_id)
        meta["status"] = "processing"
        self._write_meta(intake_id, meta)
        ocr = await self.ocr.extract_text(intake_id, meta["path"], meta["mime_type"])
        extracted = extract_document_fields(ocr.extracted_text_preview)
        meta["ocr"] = ocr.model_dump()
        meta["extracted"] = extracted.model_dump()
        meta["status"] = "processed"
        self._write_meta(intake_id, meta)
        preview = await self.mapper.build_mapping_preview(intake_id, extracted, cookies, user, ocr.extracted_text_preview)
        meta["mapping_preview"] = preview.model_dump(mode="json")
        self._write_meta(intake_id, meta)
        await log_audit_event(AuditEvent(user=user, action="document_intake_processed", tool_name="document_intake", allowed=True, risk_level="medium", input_summary=intake_id, output_summary=preview.target_doctype))
        return preview

    async def get(self, intake_id: str) -> dict[str, Any]:
        return self._public(self._meta(intake_id))

    async def ocr_result(self, intake_id: str) -> OCRResult:
        meta = self._meta(intake_id)
        if "ocr" not in meta:
            raise AppError("Document has not been processed yet.", 409)
        return OCRResult(**meta["ocr"])

    async def mapping_preview(self, intake_id: str) -> DocumentMappingPreview:
        meta = self._meta(intake_id)
        if "mapping_preview" not in meta:
            raise AppError("Mapping preview is not available yet. Process the document first.", 409)
        return DocumentMappingPreview(**meta["mapping_preview"])

    async def update_mapping_preview(self, intake_id: str, request: UpdateMappingPreviewRequest, cookies: dict | None = None, user: str = "unknown") -> DocumentMappingPreview:
        meta = self._meta(intake_id)
        preview = await self.mapper.rebuild_from_edited_payload(
            intake_id,
            meta.get("extracted", {}).get("source_document_type") or meta.get("mapping_preview", {}).get("source_document_type") or "unknown",
            request.target_doctype,
            request.draft_payload,
            cookies,
            user,
            meta.get("ocr", {}).get("extracted_text_preview"),
            meta.get("extracted", {}).get("warnings") or [],
        )
        meta["mapping_preview"] = preview.model_dump(mode="json")
        meta["status"] = "edited"
        self._write_meta(intake_id, meta)
        return preview

    async def confirm_create(self, intake_id: str, cookies: dict | None = None, user: str = "unknown"):
        preview = await self.mapping_preview(intake_id)
        if not preview.valid:
            raise AppError(preview.invalid_reason or "Required fields are missing before draft creation.", 422)
        if not preview.confirmation_id:
            raise AppError("Missing confirmation. Fix required fields and generate a new preview.", 409)
        return await crud_service.confirm(preview.confirmation_id, cookies, user)

    async def cancel(self, intake_id: str, user: str = "unknown") -> bool:
        meta = self._meta(intake_id)
        meta["status"] = "cancelled"
        self._write_meta(intake_id, meta)
        await log_audit_event(AuditEvent(user=user, action="document_intake_cancelled", tool_name="document_intake", allowed=True, risk_level="low", input_summary=intake_id))
        return True

    def _meta(self, intake_id: str) -> dict[str, Any]:
        if "/" in intake_id or "\\" in intake_id or ".." in intake_id:
            raise AppError("Invalid intake id.", 400)
        path = self.root / intake_id / "metadata.json"
        if not path.exists():
            raise AppError("Document intake was not found.", 404)
        return json.loads(path.read_text())

    def _write_meta(self, intake_id: str, data: dict[str, Any]) -> None:
        directory = self.root / intake_id
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "metadata.json").write_text(json.dumps(data, indent=2, default=str))

    @staticmethod
    def _public(meta: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in meta.items() if key != "path"}


document_intake_service = DocumentIntakeService()
