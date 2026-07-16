from __future__ import annotations

import re
from typing import Any

from app.schemas.document_intake import ExtractedLineItem
from app.utils.amount_parser import parse_amount
from app.utils.ocr_text_cleaner import normalize_ocr_lines

ITEM_HEADER_ALIASES = {
    "item": ["item", "item code", "code", "sku", "part no"],
    "description": ["description", "desc", "details", "product", "particulars"],
    "qty": ["qty", "quantity", "qnty"],
    "uom": ["uom", "unit"],
    "rate": ["rate", "price", "unit price"],
    "amount": ["amount", "total", "line total", "value"],
}


def extract_line_items_from_tables(tables: list[dict[str, Any]] | None) -> list[ExtractedLineItem]:
    output: list[ExtractedLineItem] = []
    for table in tables or []:
        rows = table.get("rows") or []
        if len(rows) < 2:
            continue
        header_index, column_map = _find_header_map(rows)
        if header_index is None:
            continue
        for row in rows[header_index + 1 :]:
            item = normalize_line_item({key: _cell(row, index) for key, index in column_map.items()})
            if item:
                item.confidence = max(item.confidence, 0.78)
                output.append(item)
            if len(output) >= 100:
                return output
    return output


def extract_line_items_from_lines(lines: list[str]) -> list[ExtractedLineItem]:
    return extract_line_items_from_text("\n".join(lines))


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


def normalize_line_item(row: dict[str, Any]) -> ExtractedLineItem | None:
    description = str(row.get("description") or row.get("item") or "").strip()
    item_code = str(row.get("item") or "").strip() or None
    qty = parse_amount(str(row.get("qty") or ""))
    rate = parse_amount(str(row.get("rate") or ""))
    amount = parse_amount(str(row.get("amount") or ""))
    if not description and not item_code:
        return None
    if amount is None and qty is not None and rate is not None:
        amount = round(qty * rate, 2)
    if amount is None and qty is None:
        return None
    return ExtractedLineItem(
        item_code=item_code if item_code and re.match(r"^[A-Z0-9][A-Z0-9._/-]{2,}$", item_code, re.I) else None,
        item_name=description or item_code,
        description=description or item_code,
        qty=qty,
        rate=rate,
        amount=amount,
        confidence=0.72,
    )


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


def _find_header_map(rows: list[list[Any]]) -> tuple[int | None, dict[str, int]]:
    for index, row in enumerate(rows[:8]):
        normalized = [_normalize_header(cell) for cell in row]
        column_map: dict[str, int] = {}
        for canonical, aliases in ITEM_HEADER_ALIASES.items():
            for column_index, value in enumerate(normalized):
                if any(alias == value or alias in value for alias in aliases):
                    column_map[canonical] = column_index
                    break
        if ("description" in column_map or "item" in column_map) and ("amount" in column_map or "rate" in column_map):
            return index, column_map
    return None, {}


def _normalize_header(value: Any) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]+", " ", str(value or "").lower())).strip()


def _cell(row: list[Any], index: int) -> str:
    if index >= len(row):
        return ""
    return str(row[index] or "").strip()
