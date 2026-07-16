from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.config import settings


INVOICE_KEYWORDS = (
    "invoice",
    "tax invoice",
    "invoice no",
    "date",
    "supplier",
    "total",
    "amount",
    "qty",
    "quantity",
    "description",
)


@dataclass
class ExtractedTextPage:
    page_number: int
    text: str
    lines: list[str]
    source: str = "pdf_text"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractedDocumentText:
    source: str
    full_text: str
    pages: list[ExtractedTextPage]
    confidence: float
    diagnostics: dict[str, Any]
    tables: list[dict[str, Any]] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["pages"] = [page.to_dict() for page in self.pages]
        data["tables"] = self.tables or []
        return data


def extract_pdf_text(file_path: str) -> ExtractedDocumentText:
    """Extract selectable PDF text first, preserving page lines and simple tables.

    pdfplumber gives the best layout/table signal when installed. pypdf is kept as
    a dependency-light fallback. Empty or weak text is returned as low confidence
    so the OCR service can decide to fall back to image OCR.
    """

    path = Path(file_path)
    diagnostics: dict[str, Any] = {
        "extractor": None,
        "errors": [],
        "pdf_text_length": 0,
        "invoice_like_keywords": [],
        "first_30_lines": [],
    }
    pages: list[ExtractedTextPage] = []
    tables: list[dict[str, Any]] = []

    try:
        import pdfplumber  # type: ignore

        diagnostics["extractor"] = "pdfplumber"
        with pdfplumber.open(str(path)) as pdf:
            for page_index, page in enumerate(pdf.pages[: settings.ocr_max_pages], start=1):
                text = page.extract_text(x_tolerance=1, y_tolerance=3) or ""
                lines = _normalize_lines(text)
                pages.append(ExtractedTextPage(page_number=page_index, text=text, lines=lines))
                try:
                    for table_index, table in enumerate(page.extract_tables() or []):
                        if table:
                            tables.append(
                                {
                                    "page": page_index,
                                    "table_index": table_index,
                                    "rows": table,
                                    "source": "pdfplumber",
                                }
                            )
                except Exception as exc:  # pragma: no cover - table extraction is best effort
                    diagnostics["errors"].append(f"pdfplumber_table_error: {type(exc).__name__}")
    except Exception as exc:
        diagnostics["errors"].append(f"pdfplumber_unavailable: {type(exc).__name__}")

    if not pages:
        try:
            from pypdf import PdfReader

            diagnostics["extractor"] = "pypdf"
            reader = PdfReader(str(path))
            for page_index, page in enumerate(reader.pages[: settings.ocr_max_pages], start=1):
                text = page.extract_text() or ""
                pages.append(ExtractedTextPage(page_number=page_index, text=text, lines=_normalize_lines(text)))
        except Exception as exc:
            diagnostics["errors"].append(f"pypdf_error: {type(exc).__name__}")

    full_text = "\n".join(page.text for page in pages).strip()
    all_lines = [line for page in pages for line in page.lines]
    keyword_hits = sorted({keyword for keyword in INVOICE_KEYWORDS if keyword in full_text.lower()})
    diagnostics["pdf_text_length"] = len(full_text)
    diagnostics["invoice_like_keywords"] = keyword_hits
    diagnostics["first_30_lines"] = all_lines[:30]
    confidence = _confidence(full_text, keyword_hits, tables)
    return ExtractedDocumentText(
        source="pdf_text",
        full_text=full_text,
        pages=pages,
        confidence=confidence,
        diagnostics=diagnostics,
        tables=tables,
    )


def is_good_pdf_text(document: ExtractedDocumentText) -> bool:
    return len(document.full_text.strip()) > 100 and bool(document.diagnostics.get("invoice_like_keywords"))


def _normalize_lines(text: str) -> list[str]:
    return [line.strip() for line in text.replace("\r", "\n").split("\n") if line.strip()]


def _confidence(text: str, keyword_hits: list[str], tables: list[dict[str, Any]]) -> float:
    if not text.strip():
        return 0.0
    score = min(0.45, len(text) / 2500)
    score += min(0.35, len(keyword_hits) * 0.06)
    if tables:
        score += 0.15
    return round(min(score, 0.95), 2)
