from __future__ import annotations

from difflib import SequenceMatcher
from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.services.erpnext_service import ERPNextService


class OcrPartyMatcher:
    def __init__(self, erp: ERPNextService | None = None):
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))

    async def match_supplier(self, extracted_text: str, extracted_name: str | None, cookies: dict | None = None) -> dict:
        return await self._match("Supplier", "supplier_name", extracted_text, extracted_name, cookies)

    async def match_customer(self, extracted_text: str, extracted_name: str | None, cookies: dict | None = None) -> dict:
        return await self._match("Customer", "customer_name", extracted_text, extracted_name, cookies)

    async def _match(self, doctype: str, label_field: str, extracted_text: str, extracted_name: str | None, cookies: dict | None) -> dict:
        query = extracted_name or _likely_name(extracted_text)
        candidates: list[dict[str, Any]] = []
        try:
            rows = (await self.erp.list_records(doctype, {}, ["name", label_field], 100, cookies=cookies)).records
        except Exception:
            rows = []
        for row in rows:
            label = str(row.get(label_field) or row.get("name") or "")
            score = _score(query or "", label)
            if query and (query.lower() in label.lower() or label.lower() in query.lower()):
                score = max(score, 0.95)
            if score >= 0.45:
                candidates.append({**row, "score": round(score, 2)})
        candidates = sorted(candidates, key=lambda item: item.get("score", 0), reverse=True)[:5]
        selected = candidates[0] if candidates and candidates[0].get("score", 0) >= 0.86 else None
        return {
            "matched": selected is not None,
            "selected": selected,
            "candidates": candidates,
            "warning": None if selected else f"{doctype} could not be confidently matched. Please select manually.",
        }


def _score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _likely_name(text: str) -> str | None:
    for line in (text or "").splitlines()[:15]:
        clean = line.strip()
        if any(word in clean.lower() for word in ("ltd", "limited", "trading", "hardware", "supplies", "company")):
            return clean
    return None
