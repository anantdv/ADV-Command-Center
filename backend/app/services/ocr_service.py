from __future__ import annotations

from pathlib import Path

from app.config import settings
from app.core.exceptions import AppError
from app.schemas.document_intake import OCRResult


class OCRService:
    async def extract_text(self, intake_id: str, file_path: str, mime_type: str) -> OCRResult:
        if not settings.enable_ocr:
            raise AppError("OCR is disabled.", 503)
        path = Path(file_path)
        text = ""
        pages = 1
        if mime_type == "application/pdf" or path.suffix.lower() == ".pdf":
            text, pages = self._pdf_text(path)
            if len(text.strip()) < 40:
                text = self._ocr_pdf(path)
        elif mime_type.startswith("image/"):
            text = self._ocr_image(path)
        elif path.suffix.lower() == ".docx":
            text = self._docx_text(path)
        else:
            raise AppError("Unsupported document format for OCR.", 415)
        if not text.strip():
            raise AppError(
                "OCR is not fully configured on this server. Please install OCR dependencies.",
                503,
                {"code": "ocr_dependency_missing"},
            )
        preview = " ".join(text.split())[:1200]
        return OCRResult(intake_id=intake_id, extracted_text_preview=preview, full_text_available=bool(text), confidence=None, page_count=pages)

    @staticmethod
    def _pdf_text(path: Path) -> tuple[str, int]:
        try:
            from pypdf import PdfReader
            reader = PdfReader(str(path))
            pages = min(len(reader.pages), settings.ocr_max_pages)
            text = "\n".join((reader.pages[i].extract_text() or "") for i in range(pages))
            return text, pages
        except Exception:
            return "", 0

    @staticmethod
    def _ocr_pdf(path: Path) -> str:
        try:
            from pdf2image import convert_from_path
            import pytesseract
            pages = convert_from_path(str(path), first_page=1, last_page=settings.ocr_max_pages)
            return "\n".join(pytesseract.image_to_string(page, lang=settings.ocr_language) for page in pages)
        except Exception:
            return ""

    @staticmethod
    def _ocr_image(path: Path) -> str:
        try:
            from PIL import Image
            import pytesseract
            return pytesseract.image_to_string(Image.open(path), lang=settings.ocr_language)
        except Exception:
            return ""

    @staticmethod
    def _docx_text(path: Path) -> str:
        try:
            from docx import Document
            document = Document(str(path))
            return "\n".join(paragraph.text for paragraph in document.paragraphs)
        except Exception:
            return ""
