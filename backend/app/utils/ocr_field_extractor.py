from __future__ import annotations

import re
from datetime import datetime

from app.schemas.document_intake import ExtractedDocumentFields, ExtractedLineItem
from app.utils.document_classifier import classify_document_type

TARGET_MAP = {
    "supplier_invoice": "Purchase Invoice",
    "customer_purchase_order": "Sales Order",
    "supplier_quotation": "Purchase Order",
    "customer_request_for_quotation": "Quotation",
    "delivery_document": "Delivery Note",
    "goods_receipt_document": "Purchase Receipt",
}


def extract_document_fields(text: str) -> ExtractedDocumentFields:
    source_type = classify_document_type(text)
    fields = ExtractedDocumentFields(source_document_type=source_type, target_doctype=TARGET_MAP.get(source_type), items=extract_line_items(text))
    fields.bill_no = _first(text, r"(?:invoice|bill)\s*(?:no|number|#)[:\s]+([A-Z0-9/-]+)")
    fields.po_no = _first(text, r"(?:po|purchase order)\s*(?:no|number|#)?[:\s]+([A-Z0-9/-]+)")
    fields.bill_date = _date(_first(text, r"(?:invoice|bill)\s*date[:\s]+([0-9A-Za-z /\-.]+)"))
    fields.po_date = _date(_first(text, r"(?:po|order)\s*date[:\s]+([0-9A-Za-z /\-.]+)"))
    fields.due_date = _date(_first(text, r"due\s*date[:\s]+([0-9A-Za-z /\-.]+)"))
    fields.currency = _first(text, r"\b(INR|USD|EUR|FJD|AUD|GBP)\b")
    fields.grand_total = _money(_first(text, r"(?:grand total|total amount|amount due)[:\s₹$]*([0-9,]+(?:\.\d+)?)"))
    fields.tax_amount = _money(_first(text, r"(?:tax|gst|vat)[:\s₹$]*([0-9,]+(?:\.\d+)?)"))
    party = _first(text, r"(?:supplier|vendor|from)[:\s]+([A-Za-z0-9 &.,'-]+)") or _first(text, r"(?:customer|buyer|bill to)[:\s]+([A-Za-z0-9 &.,'-]+)")
    if source_type in {"supplier_invoice", "supplier_quotation", "goods_receipt_document"}:
        fields.supplier = party
    elif source_type in {"customer_purchase_order", "customer_request_for_quotation", "delivery_document"}:
        fields.customer = party
    if not fields.items:
        fields.warnings.append("Line items could not be confidently extracted. Please review and enter items manually.")
    return fields


def extract_line_items(text: str) -> list[ExtractedLineItem]:
    items: list[ExtractedLineItem] = []
    pattern = re.compile(r"(?P<code>ITEM[-\w]+)?\s*(?P<desc>[A-Za-z][A-Za-z0-9 .,/&-]{2,})\s+(?P<qty>\d+(?:\.\d+)?)\s+(?P<rate>\d+(?:,\d{3})*(?:\.\d+)?)\s+(?P<amount>\d+(?:,\d{3})*(?:\.\d+)?)", re.I)
    for match in pattern.finditer(text):
        desc = " ".join(match.group("desc").split())[:180]
        items.append(ExtractedLineItem(item_code=match.group("code"), item_name=desc, description=desc, qty=float(match.group("qty")), rate=_money(match.group("rate")), amount=_money(match.group("amount"))))
        if len(items) >= 50:
            break
    return items


def _first(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return match.group(1).strip() if match else None


def _money(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value.replace(",", ""))
    except ValueError:
        return None


def _date(value: str | None) -> str | None:
    if not value:
        return None
    cleaned = value.strip().splitlines()[0].strip()
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y", "%d %b %Y", "%d %B %Y"):
        try:
            return datetime.strptime(cleaned[:20], fmt).date().isoformat()
        except ValueError:
            pass
    return cleaned[:20]
