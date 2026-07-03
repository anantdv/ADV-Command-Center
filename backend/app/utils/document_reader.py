from pathlib import Path

from app.config import settings
from app.core.exceptions import AppError

SUPPORTED_SUFFIXES = {".pdf", ".docx", ".html", ".htm", ".md", ".markdown", ".txt"}


def _safe_path(path: str) -> Path:
    candidate = Path(path).resolve()
    if not candidate.is_file():
        raise AppError("Knowledge document was not found.", 404)
    if candidate.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise AppError("Unsupported knowledge document format.", 422)
    if candidate.stat().st_size > settings.knowledge_max_file_bytes:
        raise AppError("Knowledge document exceeds the maximum file size.", 413)
    return candidate


def extract_text_from_pdf(path: str) -> str:
    from pypdf import PdfReader
    return "\n\n".join(page.extract_text() or "" for page in PdfReader(path).pages).strip()


def extract_text_from_docx(path: str) -> str:
    from docx import Document
    return "\n\n".join(p.text for p in Document(path).paragraphs if p.text.strip())


def extract_text_from_html(path: str) -> str:
    from bs4 import BeautifulSoup
    return BeautifulSoup(Path(path).read_text(encoding="utf-8", errors="replace"), "html.parser").get_text("\n", strip=True)


def extract_text_from_markdown(path: str) -> str:
    from bs4 import BeautifulSoup
    from markdown import markdown
    html = markdown(Path(path).read_text(encoding="utf-8", errors="replace"))
    return BeautifulSoup(html, "html.parser").get_text("\n", strip=True)


def extract_text_from_txt(path: str) -> str:
    return Path(path).read_text(encoding="utf-8", errors="replace")


def extract_text(path: str, mime_type: str | None = None) -> str:
    del mime_type
    candidate = _safe_path(path)
    suffix = candidate.suffix.lower()
    readers = {
        ".pdf": extract_text_from_pdf,
        ".docx": extract_text_from_docx,
        ".html": extract_text_from_html,
        ".htm": extract_text_from_html,
        ".md": extract_text_from_markdown,
        ".markdown": extract_text_from_markdown,
        ".txt": extract_text_from_txt,
    }
    text = readers[suffix](str(candidate)).strip()
    if not text:
        raise AppError("The document contains no extractable text. OCR is not enabled.", 422)
    return text
