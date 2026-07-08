from __future__ import annotations

from typing import Any


REPORT_SOURCES: dict[str, dict[str, Any]] = {
    "Customer": {"source_type": "doctype", "label": "Customer", "category": "Selling", "allow_detail": True, "allow_summary": True, "default_date_field": "creation"},
    "Supplier": {"source_type": "doctype", "label": "Supplier", "category": "Buying", "allow_detail": True, "allow_summary": True, "default_date_field": "creation"},
    "Item": {"source_type": "doctype", "label": "Item", "category": "Stock", "allow_detail": True, "allow_summary": True, "default_date_field": "creation"},
    "Sales Invoice": {"source_type": "doctype", "label": "Sales Invoice", "category": "Accounts", "allow_detail": True, "allow_summary": True, "default_date_field": "posting_date"},
    "Purchase Invoice": {"source_type": "doctype", "label": "Purchase Invoice", "category": "Accounts", "allow_detail": True, "allow_summary": True, "default_date_field": "posting_date"},
    "Sales Order": {"source_type": "doctype", "label": "Sales Order", "category": "Selling", "allow_detail": True, "allow_summary": True, "default_date_field": "transaction_date"},
    "Purchase Order": {"source_type": "doctype", "label": "Purchase Order", "category": "Buying", "allow_detail": True, "allow_summary": True, "default_date_field": "transaction_date"},
    "Quotation": {"source_type": "doctype", "label": "Quotation", "category": "Selling", "allow_detail": True, "allow_summary": True, "default_date_field": "transaction_date"},
    "Delivery Note": {"source_type": "doctype", "label": "Delivery Note", "category": "Stock", "allow_detail": True, "allow_summary": True, "default_date_field": "posting_date"},
    "Purchase Receipt": {"source_type": "doctype", "label": "Purchase Receipt", "category": "Stock", "allow_detail": True, "allow_summary": True, "default_date_field": "posting_date"},
    "Material Request": {"source_type": "doctype", "label": "Material Request", "category": "Stock", "allow_detail": True, "allow_summary": True, "default_date_field": "transaction_date"},
    "Issue": {"source_type": "doctype", "label": "Issue", "category": "Support", "allow_detail": True, "allow_summary": True, "default_date_field": "creation"},
}


SOURCE_ALIASES = {
    "customers": "Customer",
    "customer": "Customer",
    "suppliers": "Supplier",
    "supplier": "Supplier",
    "items": "Item",
    "item": "Item",
    "stock item": "Item",
    "stock items": "Item",
    "sales invoices": "Sales Invoice",
    "sales invoice": "Sales Invoice",
    "invoices": "Sales Invoice",
    "invoice": "Sales Invoice",
    "unpaid invoices": "Sales Invoice",
    "purchase invoices": "Purchase Invoice",
    "purchase invoice": "Purchase Invoice",
    "purchase orders": "Purchase Order",
    "purchase order": "Purchase Order",
    "sales orders": "Sales Order",
    "sales order": "Sales Order",
    "quotations": "Quotation",
    "quotation": "Quotation",
    "quotes": "Quotation",
    "quote": "Quotation",
    "delivery notes": "Delivery Note",
    "purchase receipts": "Purchase Receipt",
    "material requests": "Material Request",
    "issues": "Issue",
}


def get_allowed_sources() -> dict[str, dict[str, Any]]:
    return REPORT_SOURCES.copy()


def is_source_allowed(source_name: str) -> bool:
    return source_name in REPORT_SOURCES


def get_default_date_field(source_name: str) -> str | None:
    return REPORT_SOURCES.get(source_name, {}).get("default_date_field")


def resolve_source_from_text(text: str) -> str | None:
    normalized = f" {' '.join(text.lower().split())} "
    for alias, source in sorted(SOURCE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if f" {alias} " in normalized:
            return source
    if "sales" in normalized or "outstanding" in normalized:
        return "Sales Invoice"
    if "purchase" in normalized:
        return "Purchase Invoice"
    return None
