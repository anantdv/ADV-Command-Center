from __future__ import annotations

import re

from app.schemas.document_intake import ExtractedLineItem
from app.utils.amount_parser import parse_amount
from app.utils.ocr_text_cleaner import normalize_ocr_lines


def extract_line_items_from_text(text: str) -> list[ExtractedLineItem]:
    lines = normalize_ocr_lines(text)
    items: list[ExtractedLineItem] = []
    in_table = False
    for line in lines:
        if re.search(r"\b(description|item|qty|quantity|rate|price|amount)\b", line, re.I):
            in_table = True
            continue
        if not in_table and len(items) == 0 and not _looks_like_item_row(line):
            continue
        parsed = _parse_line_item(line)
        if parsed:
            items.append(parsed)
        elif in_table and re.search(r"\b(subtotal|total|tax|vat|gst)\b", line, re.I):
            break
        if len(items) >= 50:
            break
    return items


def extract_possible_item_lines(text: str) -> list[ExtractedLineItem]:
    """Low-confidence fallback for invoice lines with amounts but weak table structure."""
    output: list[ExtractedLineItem] = []
    for line in normalize_ocr_lines(text):
        if not _looks_like_item_row(line):
            continue
        item = _parse_line_item(line)
        if item:
            item.confidence = 0.35
            item.warning = "Low confidence line item. Please review before creating draft."
            output.append(item)
    return output


def _parse_line_item(line: str) -> ExtractedLineItem | None:
    tokens = line.split()
    numeric_positions = [(index, parse_amount(token)) for index, token in enumerate(tokens)]
    numeric_positions = [(index, value) for index, value in numeric_positions if value is not None]
    if len(numeric_positions) < 2:
        return None
    amount_index, amount = numeric_positions[-1]
    rate_index, rate = numeric_positions[-2]
    qty = numeric_positions[-3][1] if len(numeric_positions) >= 3 else None
    qty_index = numeric_positions[-3][0] if len(numeric_positions) >= 3 else rate_index
    if amount is None or rate is None:
        return None
    head = tokens[:qty_index]
    if not head:
        return None
    code = head[0] if re.match(r"^[A-Z0-9][A-Z0-9._/-]{2,}$", head[0], re.I) else None
    desc_tokens = head[1:] if code else head
    description = " ".join(desc_tokens).strip()
    if len(description) < 2:
        return None
    return ExtractedLineItem(
        item_code=code,
        item_name=description,
        description=description,
        qty=qty,
        rate=rate,
        amount=amount,
        confidence=0.68,
    )


def _looks_like_item_row(line: str) -> bool:
    if re.search(r"\b(subtotal|total|tax|vat|gst|invoice|sold to|bill to)\b", line, re.I):
        return False
    numbers = re.findall(r"\b\d[\d,]*(?:\.\d+)?\b", line)
    words = re.findall(r"[A-Za-z]{2,}", line)
    return len(numbers) >= 3 and len(words) >= 1
