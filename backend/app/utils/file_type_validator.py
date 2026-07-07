from __future__ import annotations

from app.core.exceptions import AppError

ALLOWED_MIME_TYPES = {"application/pdf", "image/png", "image/jpeg", "image/jpg", "text/plain"}
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".txt"}


def validate_upload(filename: str, mime_type: str | None, size_bytes: int, max_size_mb: int) -> None:
    lowered = filename.lower()
    if not any(lowered.endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise AppError("Unsupported file type. Upload PDF, PNG, JPG, JPEG, or TXT.", 415)
    if mime_type and mime_type not in ALLOWED_MIME_TYPES:
        raise AppError("Unsupported MIME type for document intake.", 415, {"mime_type": mime_type})
    if size_bytes > max_size_mb * 1024 * 1024:
        raise AppError(f"File is too large. Maximum size is {max_size_mb} MB.", 413)
