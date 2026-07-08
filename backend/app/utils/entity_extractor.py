from __future__ import annotations

import re
from typing import Any


RECORD_ID_PATTERN = re.compile(
    r"\b(?:ACC-SINV|SINV|PINV|SAL-ORD|PUR-ORD|SAL-QTN|ITEM|CUST|SUPP)-[A-Z0-9-]+\b",
    re.IGNORECASE,
)

STOP_SUFFIX = re.compile(
    r"\b(?:for|from|in|during|between|above|below|under|over|greater|less|this|last|today|yesterday|month|year|valued|value|amount|total)\b",
    re.IGNORECASE,
)


def extract_record_name(message: str, doctype: str) -> str | None:
    known = RECORD_ID_PATTERN.search(message)
    if known:
        return known.group(0).upper()
    return None


def extract_entity_filters(message: str, doctype: str) -> dict[str, Any]:
    """Extract safe fuzzy entity filters from common natural language phrases."""

    text = " ".join(message.strip().split())
    if doctype == "Customer":
        entity = _first_match(
            text,
            [
                r"\bcustomer\s+name\s+(.+)$",
                r"\bcustomer\s+called\s+(.+)$",
                r"\bcustomer\s+(.+)$",
                r"\bclient\s+(.+)$",
            ],
        )
        return {"customer_name": ["like", f"%{entity}%"]} if entity else {}

    if doctype == "Supplier":
        country = _first_match(text, [r"\b(?:supplier|suppliers|vendor|vendors)\s+from\s+(.+)$"])
        if country:
            return {"country": country}
        entity = _first_match(
            text,
            [
                r"\bsupplier\s+name\s+(.+)$",
                r"\bsupplier\s+called\s+(.+)$",
                r"\bsupplier\s+(.+)$",
                r"\bvendor\s+(.+)$",
            ],
        )
        return {"supplier_name": ["like", f"%{entity}%"]} if entity else {}

    if doctype == "Item":
        entity = _first_match(
            text,
            [
                r"\b(?:items?|products?)\s+(?:containing|called|named)\s+(.+)$",
                r"\b(?:item|product)\s+(.+)$",
            ],
        )
        return {"item_name": ["like", f"%{entity}%"]} if entity else {}

    if doctype == "Sales Invoice":
        record = extract_record_name(text, doctype)
        if record:
            return {"name": record}
        customer = _first_match(text, [r"\b(?:invoices?|sales invoices?)\s+for\s+customer\s+(.+)$", r"\bfor\s+customer\s+(.+)$"])
        return {"customer": ["like", f"%{customer}%"]} if customer else {}

    if doctype == "Purchase Invoice":
        record = extract_record_name(text, doctype)
        if record:
            return {"name": record}
        supplier = _first_match(text, [r"\b(?:purchase invoices?|vendor bills?|supplier invoices?)\s+for\s+(?:supplier|vendor)\s+(.+)$", r"\bfor\s+(?:supplier|vendor)\s+(.+)$"])
        return {"supplier": ["like", f"%{supplier}%"]} if supplier else {}

    if doctype == "Quotation":
        customer = _first_match(text, [r"\bquotations?\s+for\s+customer\s+(.+)$", r"\bquotes?\s+for\s+customer\s+(.+)$", r"\bfor\s+customer\s+(.+)$"])
        return {"party_name": ["like", f"%{customer}%"]} if customer else {}

    if doctype == "Sales Order":
        customer = _first_match(text, [r"\b(?:sales orders?|customer po)\s+for\s+(.+)$", r"\bfor\s+customer\s+(.+)$"])
        return {"customer": ["like", f"%{customer}%"]} if customer else {}

    if doctype == "Purchase Order":
        supplier = _first_match(text, [r"\bpurchase orders?\s+for\s+(?:supplier|vendor)?\s*(.+)$", r"\bfor\s+(?:supplier|vendor)\s+(.+)$"])
        return {"supplier": ["like", f"%{supplier}%"]} if supplier else {}

    return {}


def _first_match(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = _clean_entity(match.group(1))
            if candidate:
                return candidate
    return None


def _clean_entity(value: str) -> str:
    value = STOP_SUFFIX.split(value, maxsplit=1)[0]
    value = re.sub(r"[\s,?.!]+$", "", value.strip())
    value = re.sub(r"^(?:name|called|named|the|a|an)\s+", "", value, flags=re.IGNORECASE)
    bad = {"show", "me", "find", "called", "name", "for", "month", "between", "above", "below", "records", "list"}
    parts = [part for part in value.split() if part.lower() not in bad]
    return " ".join(parts).strip()
