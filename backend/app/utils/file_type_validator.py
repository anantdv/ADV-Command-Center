from __future__ import annotations

from app.core.exceptions import AppError

ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg", "image/webp", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp", ".docx"}


def validate_upload(filename: str, mime_type: str | None, size_bytes: int, max_size_mb: int) -> None:
    lowered = filename.lower()
    if not any(lowered.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise AppError("This file type is not supported for OCR intake.", 415, {"code": "invalid_file_type"})
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        raise AppError("This file type is not supported for OCR intake.", 415, {"code": "invalid_file_type", "mime_type": mime_type})
    if size_bytes > max_size_mb * 1024 * 1024:
        raise AppError(f"File is too large. Maximum size is {max_size_mb} MB.", 413, {"code": "file_too_large"})
