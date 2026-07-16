from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.config import settings


@dataclass
class OcrTextBlock:
    text: str
    page: int
    x: float | None = None
    y: float | None = None
    width: float | None = None
    height: float | None = None
    confidence: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OcrLayoutResult:
    full_text: str
    lines: list[str]
    blocks: list[OcrTextBlock]
    tables: list[dict[str, Any]]
    diagnostics: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blocks"] = [block.to_dict() for block in self.blocks]
        return data


def extract_ocr_layout(file_path: str) -> OcrLayoutResult:
    """Extract OCR text with basic line grouping from word-level Tesseract data."""

    path = Path(file_path)
    diagnostics: dict[str, Any] = {"errors": [], "ocr_text_length": 0, "first_50_lines": []}
    blocks: list[OcrTextBlock] = []
    try:
        images = _images_for_path(path)
        for page_index, image in enumerate(images, start=1):
            blocks.extend(_ocr_image_blocks(image, page_index))
    except Exception as exc:
        diagnostics["errors"].append(f"ocr_layout_error: {type(exc).__name__}")
        text = _fallback_text(path, diagnostics)
        lines = _normalize_lines(text)
        diagnostics["ocr_text_length"] = len(text)
        diagnostics["first_50_lines"] = lines[:50]
        return OcrLayoutResult(full_text=text, lines=lines, blocks=[], tables=[], diagnostics=diagnostics)

    lines = _blocks_to_lines(blocks)
    full_text = "\n".join(lines)
    diagnostics["ocr_text_length"] = len(full_text)
    diagnostics["first_50_lines"] = lines[:50]
    return OcrLayoutResult(full_text=full_text, lines=lines, blocks=blocks, tables=[], diagnostics=diagnostics)


def _images_for_path(path: Path) -> list[Any]:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        from pdf2image import convert_from_path

        return convert_from_path(str(path), first_page=1, last_page=settings.ocr_max_pages)
    from PIL import Image

    return [Image.open(path)]


def _ocr_image_blocks(image: Any, page: int) -> list[OcrTextBlock]:
    import pytesseract

    data = pytesseract.image_to_data(image, lang=settings.ocr_language, output_type=pytesseract.Output.DICT)
    blocks: list[OcrTextBlock] = []
    for index, text in enumerate(data.get("text") or []):
        word = str(text or "").strip()
        if not word:
            continue
        try:
            confidence = float(data.get("conf", [None])[index])
        except Exception:
            confidence = None
        if confidence is not None and confidence < 0:
            confidence = None
        blocks.append(
            OcrTextBlock(
                text=word,
                page=page,
                x=float(data.get("left", [0])[index]),
                y=float(data.get("top", [0])[index]),
                width=float(data.get("width", [0])[index]),
                height=float(data.get("height", [0])[index]),
                confidence=confidence,
            )
        )
    return blocks


def _blocks_to_lines(blocks: list[OcrTextBlock]) -> list[str]:
    grouped: dict[tuple[int, int], list[OcrTextBlock]] = {}
    for block in blocks:
        y_bucket = int(round((block.y or 0) / 8))
        grouped.setdefault((block.page, y_bucket), []).append(block)
    lines: list[str] = []
    for _, words in sorted(grouped.items(), key=lambda item: (item[0][0], item[0][1])):
        text = " ".join(block.text for block in sorted(words, key=lambda word: word.x or 0)).strip()
        if text:
            lines.append(text)
    return lines


def _fallback_text(path: Path, diagnostics: dict[str, Any]) -> str:
    try:
        import pytesseract

        if path.suffix.lower() == ".pdf":
            from pdf2image import convert_from_path

            pages = convert_from_path(str(path), first_page=1, last_page=settings.ocr_max_pages)
            return "\n".join(pytesseract.image_to_string(page, lang=settings.ocr_language) for page in pages)
        from PIL import Image

        return pytesseract.image_to_string(Image.open(path), lang=settings.ocr_language)
    except Exception as exc:
        diagnostics["errors"].append(f"ocr_text_fallback_error: {type(exc).__name__}")
        return ""


def _normalize_lines(text: str) -> list[str]:
    return [line.strip() for line in text.replace("\r", "\n").split("\n") if line.strip()]
