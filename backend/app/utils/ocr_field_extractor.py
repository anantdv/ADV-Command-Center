import re
from datetime import date

from app.schemas.document_intake import ExtractedDocumentFields, ExtractedLineItem
from app.utils.amount_parser import extract_amount_after_labels
from app.utils.document_classifier import classify_document_type
from app.utils.date_parser import parse_any_date
from app.utils.ocr_line_item_extractor import extract_line_items_from_text
from app.utils.ocr_text_cleaner import clean_ocr_text, normalize_ocr_lines

TARGET_MAP = {
    "supplier_invoice": "Purchase Invoice",
    "customer_purchase_order": "Sales Order",
    "supplier_quotation": "Purchase Order",
    "customer_request_for_quotation": "Quotation",
    "delivery_document": "Delivery Note",
    "goods_receipt_document": "Purchase Receipt",
}

LABEL_WORDS = {
    "invoice", "invoice no", "invoice number", "inv no", "bill no", "bill number",
    "date", "invoice date", "bill date", "supplier", "vendor", "customer", "buyer",
    "ship to", "bill to", "address", "phone", "fax", "email", "tin", "vat", "gst",
    "subtotal", "tax", "vat amount", "grand total", "total", "amount", "qty",
    "quantity", "rate", "price", "description", "item", "uom",
}


def extract_document_fields(text: str) -> ExtractedDocumentFields:
    cleaned = clean_ocr_text(text)
    lines = normalize_ocr_lines(cleaned)
    source_type = classify_document_type(cleaned)
    fields = ExtractedDocumentFields(source_document_type=source_type, target_doctype=TARGET_MAP.get(source_type), items=extract_line_items(cleaned))
    fields.bill_no, bill_conf = extract_document_number(lines, ["supplier invoice no", "invoice no", "invoice number", "invoice #", "bill no", "bill number"])
    fields.po_no, _ = extract_document_number(lines, ["purchase order no", "po no", "po number", "order no"])
    fields.bill_date, date_conf = extract_document_date(lines, ["invoice date", "bill date", "date"])
    fields.posting_date = date.today().isoformat()
    fields.po_date, _ = extract_document_date(lines, ["po date", "order date"])
    fields.due_date, _ = extract_document_date(lines, ["due date"])
    totals = extract_currency_and_totals(lines)
    fields.currency = totals.get("currency")
    fields.grand_total = totals.get("grand_total")
    fields.tax_amount = totals.get("tax_amount")
    party = _extract_party(lines)
    if source_type in {"supplier_invoice", "supplier_quotation", "goods_receipt_document"}:
        fields.supplier = party
    elif source_type in {"customer_purchase_order", "customer_request_for_quotation", "delivery_document"}:
        fields.customer = party
    if not fields.bill_no and source_type == "supplier_invoice":
        fields.warnings.append("Could not confidently extract invoice number.")
    if not fields.bill_date and source_type == "supplier_invoice":
        fields.warnings.append("Could not confidently extract invoice date.")
    if bill_conf == 0:
        fields.warnings.append('The extracted value looked like a label, so it was not used as Bill No.')
    if date_conf == 0:
        fields.warnings.append('The extracted date candidate looked like a label, so it was not used as Bill Date.')
    if not fields.items:
        fields.warnings.append("I could not detect line items. Please add them manually before creating the draft.")
    return fields


def extract_line_items(text: str) -> list[ExtractedLineItem]:
    return extract_line_items_from_text(text)


def is_label_like(value: str | None) -> bool:
    if not value:
        return True
    normalized = re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    if normalized in LABEL_WORDS:
        return True
    if normalized in {"fax", "phone", "email", "invoice no", "bill date"}:
        return True
    if len(normalized) < 2 and not normalized.isdigit():
        return True
    return False


def extract_document_number(lines: list[str], labels: list[str]) -> tuple[str | None, float]:
    for index, line in enumerate(lines):
        for label in labels:
            inline = re.search(rf"\b{re.escape(label)}\.?\s*:?\s*#?\s*([A-Z0-9][A-Z0-9._/-]{{2,}})\b", line, flags=re.I)
            if inline:
                candidate = _clean_value(inline.group(1))
                if _valid_doc_number(candidate):
                    return candidate, 0.88
                return None, 0.0
            if re.fullmatch(rf"{re.escape(label)}\.?\s*:?", line, flags=re.I) and index + 1 < len(lines):
                candidate = _clean_value(lines[index + 1])
                if _valid_doc_number(candidate):
                    return candidate, 0.72
                return None, 0.0
    return None, 0.0


def extract_document_date(lines: list[str], labels: list[str]) -> tuple[str | None, float]:
    for index, line in enumerate(lines):
        for label in labels:
            inline = re.search(rf"\b{re.escape(label)}\.?\s*:?\s*([0-9]{{1,4}}[0-9A-Za-z ,./-]{{3,24}})", line, flags=re.I)
            if inline:
                raw = _clean_value(inline.group(1))
                if is_label_like(raw):
                    return None, 0.0
                parsed = parse_any_date(raw)
                if parsed:
                    return parsed, 0.86
            if re.fullmatch(rf"{re.escape(label)}\.?\s*:?", line, flags=re.I) and index + 1 < len(lines):
                raw = _clean_value(lines[index + 1])
                if is_label_like(raw):
                    return None, 0.0
                parsed = parse_any_date(raw)
                if parsed:
                    return parsed, 0.7
    return None, 0.0


def extract_currency_and_totals(lines: list[str]) -> dict:
    joined = "\n".join(lines)
    currency = _first(joined, r"\b(PGK|FJD|USD|EUR|AUD|INR|GBP)\b")
    return {
        "currency": currency,
        "grand_total": extract_amount_after_labels(lines, ["grand total", "total amount", "amount due", "balance due", "total"]),
        "tax_amount": extract_amount_after_labels(lines, ["tax", "gst", "vat", "vat amount"]),
    }


def _extract_party(lines: list[str]) -> str | None:
    for index, line in enumerate(lines[:20]):
        match = re.search(r"\b(?:supplier|vendor|from|customer|buyer|bill to)\b\s*:?\s*(.+)$", line, re.I)
        if match:
            candidate = _clean_party(match.group(1))
            if candidate and not is_label_like(candidate):
                return candidate
        if re.fullmatch(r"(?:supplier|vendor|from|customer|buyer|bill to)\s*:?", line, re.I) and index + 1 < len(lines):
            candidate = _clean_party(lines[index + 1])
            if candidate and not is_label_like(candidate):
                return candidate
    # Many invoices put company name in top lines without a label.
    for line in lines[:8]:
        candidate = _clean_party(line)
        if candidate and re.search(r"\b(ltd|limited|inc|corp|company|trading|hardware|supplies|enterprise)\b", candidate, re.I):
            return candidate
    return None


def _first(text: str, pattern: str) -> str | None:
    match = re.search(pattern, text, re.I)
    return match.group(1).strip() if match else None


def _clean_value(value: str) -> str:
    return re.split(r"\s{2,}|\t", value.strip())[0].strip(" :#")


def _valid_doc_number(value: str | None) -> bool:
    if not value or is_label_like(value):
        return False
    if not re.search(r"\d", value):
        return False
    return bool(re.fullmatch(r"[A-Z0-9][A-Z0-9._/-]{2,}", value, flags=re.I))


def _clean_party(value: str) -> str | None:
    text = value.strip(" :-")
    if not text or is_label_like(text):
        return None
    if re.search(r"\b(phone|fax|email|invoice|date|total|tax)\b", text, re.I):
        return None
    return text[:120]
