from __future__ import annotations

import re


DOCTYPE_ALIASES = {
    "customer": "Customer",
    "customers": "Customer",
    "client": "Customer",
    "clients": "Customer",
    "supplier": "Supplier",
    "suppliers": "Supplier",
    "vendor": "Supplier",
    "vendors": "Supplier",
    "item": "Item",
    "items": "Item",
    "product": "Item",
    "products": "Item",
    "sku": "Item",
    "stock item": "Item",
    "invoice": "Sales Invoice",
    "invoices": "Sales Invoice",
    "sales invoice": "Sales Invoice",
    "sales invoices": "Sales Invoice",
    "customer invoice": "Sales Invoice",
    "customer invoices": "Sales Invoice",
    "purchase invoice": "Purchase Invoice",
    "purchase invoices": "Purchase Invoice",
    "supplier invoice": "Purchase Invoice",
    "supplier invoices": "Purchase Invoice",
    "vendor invoice": "Purchase Invoice",
    "vendor invoices": "Purchase Invoice",
    "vendor bill": "Purchase Invoice",
    "vendor bills": "Purchase Invoice",
    "purchase bill": "Purchase Invoice",
    "purchase bills": "Purchase Invoice",
    "quotation": "Quotation",
    "quotations": "Quotation",
    "quote": "Quotation",
    "quotes": "Quotation",
    "estimate": "Quotation",
    "sales order": "Sales Order",
    "sales orders": "Sales Order",
    "customer po": "Sales Order",
    "customer purchase order": "Sales Order",
    "purchase order": "Purchase Order",
    "purchase orders": "Purchase Order",
    "supplier po": "Purchase Order",
    "supplier purchase order": "Purchase Order",
    "delivery note": "Delivery Note",
    "delivery notes": "Delivery Note",
    "purchase receipt": "Purchase Receipt",
    "purchase receipts": "Purchase Receipt",
    "material request": "Material Request",
    "material requests": "Material Request",
    "lead": "Lead",
    "leads": "Lead",
    "opportunity": "Opportunity",
    "opportunities": "Opportunity",
    "issue": "Issue",
    "issues": "Issue",
    "ticket": "Issue",
    "support ticket": "Issue",
    "project": "Project",
    "projects": "Project",
    "task": "Task",
    "tasks": "Task",
    "employee": "Employee",
    "employees": "Employee",
}

ALLOWED_QUERY_DOCTYPES = set(DOCTYPE_ALIASES.values())


def resolve_doctype(message: str, llm_doctype: str | None = None) -> str | None:
    """Resolve a user phrase or LLM candidate into a supported ERPNext DocType."""

    if llm_doctype in ALLOWED_QUERY_DOCTYPES:
        return llm_doctype

    text = " ".join(message.lower().split())
    if re.search(r"\b(?:purchase|supplier|vendor)\s+(?:invoice|invoices|bill|bills)\b", text):
        return "Purchase Invoice"
    if re.search(r"\b(?:customer\s+po|customer\s+purchase\s+order)\b", text):
        return "Sales Order"

    # Longest alias first avoids "invoice" winning before "purchase invoice".
    for alias, doctype in sorted(DOCTYPE_ALIASES.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return doctype
    return None
