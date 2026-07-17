import re
from datetime import date
from typing import Any

from app.schemas.document_intake import ExtractedDocumentFields, ExtractedLineItem
from app.utils.amount_parser import extract_amount_after_labels, parse_amount
from app.utils.document_classifier import classify_document_type
from app.utils.date_parser import parse_any_date
from app.utils.ocr_line_item_extractor import extract_line_items_from_tables, extract_line_items_from_text, extract_possible_item_lines
from app.utils.ocr_party_matcher import extract_likely_supplier_names_from_header
from app.utils.ocr_text_cleaner import clean_ocr_text, normalize_ocr_lines

TARGET_MAP = {
    "supplier_invoice": "Purchase Invoice",
    "customer_purchase_order": "Sales Order",
    "supplier_quotation": "Purchase Order",
    "customer_request_for_quotation": "Quotation",
    "delivery_document": "Delivery Note",
    "goods_receipt_document": "Purchase Receipt",
}

INVALID_VALUES = {
    "fax", "phone", "invoice no", "invoice number", "bill date", "date",
    "supplier", "customer", "sold to", "bill to", "email", "tax invoice",
}

LABEL_WORDS = {
    "invoice", "invoice no", "invoice number", "inv no", "bill no", "bill number",
    "date", "invoice date", "bill date", "supplier", "vendor", "customer", "buyer",
    "ship to", "bill to", "address", "phone", "fax", "email", "tin", "vat", "gst",
    "subtotal", "tax", "vat amount", "grand total", "total", "amount", "qty",
    "quantity", "rate", "price", "description", "item", "uom",
}


def extract_document_fields(text: str, lines: list[str] | None = None, tables: list[dict[str, Any]] | None = None, forced_source_type: str | None = None) -> ExtractedDocumentFields:
    cleaned = clean_ocr_text(text)
    lines = normalize_ocr_lines("\n".join(lines or []) or cleaned)
    source_type = forced_source_type or classify_document_type(cleaned)
    candidates = extract_field_candidates(lines)
    fields = ExtractedDocumentFields(source_document_type=source_type, target_doctype=TARGET_MAP.get(source_type), items=extract_line_items(cleaned, lines, tables))
    bill = select_best_candidate(candidates.get("bill_no", []), "bill_no")
    bill_conf = float(bill.get("confidence", 0)) if bill else 0.0
    fields.bill_no = bill.get("value") if bill else None
    fields.po_no, _ = extract_document_number(lines, ["purchase order no", "po no", "po number", "order no"])
    bill_date = select_best_candidate(candidates.get("bill_date", []), "bill_date")
    date_conf = float(bill_date.get("confidence", 0)) if bill_date else 0.0
    fields.bill_date = bill_date.get("value") if bill_date else None
    fields.posting_date = date.today().isoformat()
    fields.po_date, _ = extract_document_date(lines, ["po date", "order date"])
    fields.due_date, _ = extract_document_date(lines, ["due date"])
    totals = extract_currency_and_totals(lines)
    fields.currency = totals.get("currency")
    grand_total = select_best_candidate(candidates.get("grand_total", []), "grand_total")
    tax_amount = select_best_candidate(candidates.get("tax_amount", []), "tax_amount")
    fields.grand_total = grand_total.get("value") if grand_total else totals.get("grand_total")
    fields.tax_amount = tax_amount.get("value") if tax_amount else totals.get("tax_amount")
    party = _extract_party(lines, supplier_only=source_type in {"supplier_invoice", "supplier_quotation", "goods_receipt_document"})
    if not party and source_type in {"supplier_invoice", "supplier_quotation", "goods_receipt_document"}:
        supplier_candidates = extract_likely_supplier_names_from_header("\n".join(lines))
        party = str(supplier_candidates[0].get("candidate_name")) if supplier_candidates else None
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


def extract_line_items(text: str, lines: list[str] | None = None, tables: list[dict[str, Any]] | None = None) -> list[ExtractedLineItem]:
    structured = extract_line_items_from_tables(tables)
    if structured:
        return structured
    structured = extract_line_items_from_text("\n".join(lines or []) or text)
    return structured or extract_possible_item_lines(text)


def extract_field_candidates(lines: list[str]) -> dict[str, list[dict[str, Any]]]:
    fields = {
        "bill_no": _candidate_label_value(lines, ["supplier invoice no", "invoice no", "invoice number", "invoice #", "bill no", "bill number"], _valid_doc_number, "document_number"),
        "bill_date": _candidate_label_value(lines, ["invoice date", "bill date"], lambda value: parse_any_date(value) is not None, "date"),
        "grand_total": _candidate_amount(lines, ["grand total", "invoice total", "total incl", "amount due", "balance due", "total"]),
        "tax_amount": _candidate_amount(lines, ["vat amount", "gst amount", "tax amount", "vat", "gst", "tax"]),
    }
    for candidate in fields["bill_date"]:
        parsed = parse_any_date(str(candidate.get("value") or ""))
        if parsed:
            candidate["raw_value"] = candidate["value"]
            candidate["value"] = parsed
    for field in ("grand_total", "tax_amount"):
        for candidate in fields[field]:
            amount = parse_amount(str(candidate.get("value") or ""))
            if amount is not None:
                candidate["raw_value"] = candidate["value"]
                candidate["value"] = amount
    return fields


def select_best_candidate(candidates: list[dict[str, Any]], fieldname: str) -> dict[str, Any] | None:
    valid = [candidate for candidate in candidates if _candidate_valid(candidate, fieldname)]
    if not valid:
        return None
    return sorted(valid, key=lambda candidate: float(candidate.get("confidence", 0)), reverse=True)[0]


def is_label_like(value: str | None) -> bool:
    if not value:
        return True
    normalized = re.sub(r"[^a-z0-9 ]+", "", value.lower()).strip()
    normalized = re.sub(r"\s+", " ", normalized)
    if normalized in LABEL_WORDS or normalized in INVALID_VALUES:
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


def _extract_party(lines: list[str], supplier_only: bool = False) -> str | None:
    labels = ["supplier", "vendor", "from"] if supplier_only else ["supplier", "vendor", "from", "customer", "buyer", "bill to"]
    for index, line in enumerate(lines[:20]):
        label_pattern = "|".join(re.escape(label) for label in labels)
        match = re.search(rf"\b(?:{label_pattern})\b\s*:?\s*(.+)$", line, re.I)
        if match:
            candidate = _clean_party(match.group(1))
            if candidate and not is_label_like(candidate):
                return candidate
        if re.fullmatch(rf"(?:{label_pattern})\s*:?", line, re.I) and index + 1 < len(lines):
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
    return re.split(r"\t", value.strip())[0].strip(" :#")


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


def _candidate_label_value(lines: list[str], labels: list[str], validator, value_type: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    label_pattern = "|".join(re.escape(label) for label in labels)
    for index, line in enumerate(lines):
        # Same line and right-side value: "Invoice No: INV-1001" or "Invoice No     INV-1001"
        match = re.search(rf"\b(?:{label_pattern})\b\s*[:#-]?\s+(.+)$", line, flags=re.I)
        if match:
            candidate = _clean_candidate_value(match.group(1), value_type)
            output.append(_candidate(candidate, 0.86, line, "same_line_label_value"))
        # Next line value.
        if re.fullmatch(rf"(?:{label_pattern})\s*[:#-]?", line.strip(), flags=re.I) and index + 1 < len(lines):
            candidate = _clean_candidate_value(lines[index + 1], value_type)
            output.append(_candidate(candidate, 0.72, f"{line} / {lines[index + 1]}", "next_line_label_value"))
        # Nearby window: previous two lines contain label, current line looks like value.
        if index > 0 and any(re.search(rf"\b(?:{label_pattern})\b", previous, flags=re.I) for previous in lines[max(0, index - 2) : index]):
            candidate = _clean_candidate_value(line, value_type)
            output.append(_candidate(candidate, 0.62, line, "nearby_label_window"))
    return [item for item in output if item["value"] and not is_label_like(str(item["value"])) and validator(str(item["value"]))]


def _candidate_amount(lines: list[str], labels: list[str]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    label_pattern = "|".join(re.escape(label) for label in labels)
    for index, line in enumerate(lines):
        if re.search(rf"\b(?:{label_pattern})\b", line, flags=re.I):
            amount = _last_amount(line)
            if amount is not None:
                output.append(_candidate(str(amount), 0.82, line, "same_line_amount_label"))
            elif index + 1 < len(lines):
                next_amount = _last_amount(lines[index + 1])
                if next_amount is not None:
                    output.append(_candidate(str(next_amount), 0.66, f"{line} / {lines[index + 1]}", "next_line_amount_label"))
    return output


def _candidate(value: str | float | None, confidence: float, source_line: str, reason: str) -> dict[str, Any]:
    return {"value": value, "confidence": confidence, "source_line": source_line[:220], "reason": reason}


def _candidate_valid(candidate: dict[str, Any], fieldname: str) -> bool:
    value = candidate.get("value")
    if value in (None, "") or is_label_like(str(value)):
        return False
    if fieldname == "bill_no":
        return _valid_doc_number(str(value))
    if fieldname == "bill_date":
        return parse_any_date(str(value)) is not None or bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value)))
    if fieldname in {"grand_total", "tax_amount"}:
        return parse_amount(str(value)) is not None or isinstance(value, (int, float))
    return True


def _clean_candidate_value(value: str, value_type: str) -> str:
    text = value.strip(" :#-")
    if value_type == "document_number":
        match = re.search(r"\b[A-Z0-9][A-Z0-9._/-]{2,}\b", text, flags=re.I)
        return match.group(0).strip(" :#-") if match else text
    if value_type == "date":
        match = re.search(r"\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{1,2}[ -][A-Za-z]{3,9}[ -]\d{2,4}|[A-Za-z]{3,9} \d{1,2},? \d{4}|\d{4}-\d{2}-\d{2})\b", text)
        return match.group(0) if match else text
    return text


def _last_amount(line: str) -> float | None:
    values = re.findall(r"(?:PGK|FJD|USD|AUD|INR|\$)?\s*[-+]?\d[\d,\s]*(?:\.\d+)?", line, flags=re.I)
    for value in reversed(values):
        parsed = parse_amount(value)
        if parsed is not None:
            return parsed
    return None
