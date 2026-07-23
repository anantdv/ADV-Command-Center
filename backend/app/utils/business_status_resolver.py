from __future__ import annotations

import re
from typing import Any


INCOMPLETE_STATUSES = ["To Receive and Bill", "To Receive", "To Bill"]
OPEN_SO_STATUSES = ["To Deliver and Bill", "To Deliver", "To Bill"]


class BusinessStatusResolver:
    """Maps natural-language business status to DocType-specific predicates."""

    def detect_term(self, text: str, doctype: str) -> str | None:
        normalized = " ".join(str(text or "").lower().split())
        if re.search(r"\bpending\s+(?:receipt|receive|receiving)\b", normalized):
            return "pending_receipt"
        if re.search(r"\bpending\s+(?:billing|bill)\b", normalized):
            return "pending_billing"
        for term in ("draft", "submitted", "pending", "open", "completed", "closed", "cancelled", "overdue", "unpaid", "paid"):
            if re.search(rf"\b{term}\b", normalized):
                return term
        return None

    def resolve(self, doctype: str, term: str | None) -> dict[str, Any]:
        if not term:
            return {}
        method = getattr(self, f"_resolve_{doctype.lower().replace(' ', '_')}", None)
        if method:
            return method(term)
        return self._generic(term)

    def _resolve_purchase_order(self, term: str) -> dict[str, Any]:
        if term == "draft":
            return {"docstatus": 0}
        if term == "submitted":
            return {"docstatus": 1}
        if term == "pending":
            return {
                "_business_status": {
                    "term": "pending",
                    "include_drafts": True,
                    "branches": [
                        {"docstatus": 0},
                        {"docstatus": 1, "status": ["in", INCOMPLETE_STATUSES]},
                        {"docstatus": 1, "per_received": ["<", 100]},
                        {"docstatus": 1, "per_billed": ["<", 100]},
                    ],
                }
            }
        if term == "pending_receipt":
            return {"docstatus": 1, "per_received": ["<", 100]}
        if term == "pending_billing":
            return {"docstatus": 1, "per_billed": ["<", 100]}
        if term == "open":
            return {"docstatus": 1, "status": ["not in", ["Closed", "Completed", "Cancelled"]]}
        return self._generic(term)

    def _resolve_sales_order(self, term: str) -> dict[str, Any]:
        if term == "draft":
            return {"docstatus": 0}
        if term == "submitted":
            return {"docstatus": 1}
        if term in {"pending", "open"}:
            return {"docstatus": 1, "status": ["in", OPEN_SO_STATUSES]}
        if term == "pending_billing":
            return {"docstatus": 1, "per_billed": ["<", 100]}
        return self._generic(term)

    def _resolve_sales_invoice(self, term: str) -> dict[str, Any]:
        if term == "draft":
            return {"docstatus": 0}
        if term == "submitted":
            return {"docstatus": 1}
        if term == "overdue":
            return {"status": "Overdue"}
        if term == "unpaid":
            return {"status": ["in", ["Unpaid", "Overdue"]]}
        if term == "paid":
            return {"outstanding_amount": ["=", 0]}
        return self._generic(term)

    def _resolve_purchase_invoice(self, term: str) -> dict[str, Any]:
        return self._resolve_sales_invoice(term)

    @staticmethod
    def _generic(term: str) -> dict[str, Any]:
        if term == "draft":
            return {"docstatus": 0}
        if term == "submitted":
            return {"docstatus": 1}
        if term in {"closed", "completed", "cancelled"}:
            return {"status": term.title()}
        return {}


business_status_resolver = BusinessStatusResolver()
