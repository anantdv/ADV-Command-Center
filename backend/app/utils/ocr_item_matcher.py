from __future__ import annotations

from difflib import SequenceMatcher

from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.document_intake import ExtractedLineItem
from app.services.erpnext_service import ERPNextService


class OcrItemMatcher:
    def __init__(self, erp: ERPNextService | None = None):
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))

    async def match_items(self, extracted_items: list[ExtractedLineItem], cookies: dict | None = None) -> list[dict]:
        try:
            rows = (await self.erp.list_records("Item", {}, ["name", "item_name", "stock_uom"], 250, cookies=cookies)).records
        except Exception:
            rows = []
        output: list[dict] = []
        for item in extracted_items:
            query = item.item_code or item.item_name or item.description or ""
            candidates = []
            for row in rows:
                score = max(_score(query, str(row.get("name") or "")), _score(query, str(row.get("item_name") or "")))
                if query and query.lower() == str(row.get("name") or "").lower():
                    score = 1.0
                if score >= 0.45:
                    candidates.append({**row, "score": round(score, 2)})
            candidates = sorted(candidates, key=lambda row: row.get("score", 0), reverse=True)[:5]
            output.append({"input": item.model_dump(), "selected": candidates[0] if candidates and candidates[0].get("score", 0) >= 0.9 else None, "candidates": candidates})
        return output


def _score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()
