from __future__ import annotations

import re
from dataclasses import dataclass

from app.utils.doctype_resolver import resolve_doctype


DOCUMENT_PREFIX_DOCTYPE_MAP = {
    "ACC-SINV": "Sales Invoice",
    "SINV": "Sales Invoice",
    "ACC-PINV": "Purchase Invoice",
    "PINV": "Purchase Invoice",
    "SAL-ORD": "Sales Order",
    "SO": "Sales Order",
    "PUR-ORD": "Purchase Order",
    "PO": "Purchase Order",
    "SAL-QTN": "Quotation",
    "QTN": "Quotation",
    "DN": "Delivery Note",
    "PR": "Purchase Receipt",
    "MAT-MR": "Material Request",
    "CUST": "Customer",
    "SUPP": "Supplier",
    "ITEM": "Item",
}

DOCUMENT_NAME_PATTERN = re.compile(
    r"\b(?:ACC-SINV|SINV|ACC-PINV|PINV|SAL-ORD|PUR-ORD|SAL-QTN|MAT-MR|CUST|SUPP|ITEM|QTN|DN|PR|SO|PO)-[A-Z0-9-]+\b",
    re.IGNORECASE,
)


@dataclass
class DetailIntent:
    matched: bool
    doctype: str | None = None
    name: str | None = None
    confidence: float = 0.0
    needs_doctype: bool = False


def parse_detail_intent(message: str) -> DetailIntent:
    text = " ".join(message.strip().split())
    lowered = text.lower()
    if re.search(r"^\s*(?:create|add|update|change|delete|remove|submit|cancel|approve|reject)\b", lowered):
        return DetailIntent(False)
    detail_requested = bool(
        re.search(r"\b(?:show|view|open|get)\b.*\b(?:detail|details|document|record)\b|\b(?:open|view|get|show)\b", lowered)
    )
    explicit_doc = DOCUMENT_NAME_PATTERN.search(text)
    if not detail_requested and not explicit_doc:
        return DetailIntent(False)
    name = explicit_doc.group(0).upper() if explicit_doc else None
    doctype = resolve_doctype(text)
    if name and not doctype:
        doctype = resolve_doctype_from_document_name(name)
    if name and doctype:
        return DetailIntent(True, doctype, name, 0.96)
    if name:
        return DetailIntent(True, None, name, 0.74, needs_doctype=True)
    return DetailIntent(False)


def resolve_doctype_from_document_name(name: str) -> str | None:
    upper = name.upper()
    for prefix, doctype in sorted(DOCUMENT_PREFIX_DOCTYPE_MAP.items(), key=lambda item: len(item[0]), reverse=True):
        if upper.startswith(f"{prefix}-"):
            return doctype
    return None
