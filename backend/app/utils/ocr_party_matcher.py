from __future__ import annotations

from difflib import SequenceMatcher
import re
from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.services.erpnext_service import ERPNextService
from app.utils.ocr_text_cleaner import normalize_ocr_lines

BUYER_LABELS = {
    "sold to", "bill to", "ship to", "customer", "buyer", "deliver to",
    "delivery to", "consignee", "attention",
}
SUPPLIER_EXCLUSION_LABELS = BUYER_LABELS | {
    "invoice no", "invoice number", "date", "fax", "phone", "email", "tin",
    "vat", "tax invoice", "invoice", "page", "qty", "amount", "total",
}
COMPANY_WORDS = {
    "ltd", "limited", "pte", "pty", "company", "trading", "freezers",
    "hardware", "supplies", "distributors", "wholesale", "enterprise",
    "corporation", "corp", "industries", "foods", "services", "motors",
    "pharmacy", "electrical", "engineering", "logistics",
}


class OcrPartyMatcher:
    def __init__(self, erp: ERPNextService | None = None):
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))

    async def match_supplier(self, extracted_text: str, extracted_name: str | None, cookies: dict | None = None) -> dict:
        header_candidates = extract_likely_supplier_names_from_header(extracted_text)
        return await self._match("Supplier", "supplier_name", extracted_text, extracted_name, cookies, header_candidates)

    async def match_customer(self, extracted_text: str, extracted_name: str | None, cookies: dict | None = None) -> dict:
        return await self._match("Customer", "customer_name", extracted_text, extracted_name, cookies, [])

    async def _match(self, doctype: str, label_field: str, extracted_text: str, extracted_name: str | None, cookies: dict | None, header_candidates: list[dict[str, Any]]) -> dict:
        queries = []
        if extracted_name:
            queries.append({"candidate_name": extracted_name, "source": "label", "confidence": 0.8})
        queries.extend(header_candidates)
        fallback = _likely_name(extracted_text)
        if fallback:
            queries.append({"candidate_name": fallback, "source": "header", "confidence": 0.55})
        candidates: list[dict[str, Any]] = []
        try:
            rows = (await self.erp.list_records(doctype, {}, ["name", label_field], 100, cookies=cookies)).records
        except Exception:
            rows = []
        for row in rows:
            label = str(row.get(label_field) or row.get("name") or "")
            best_score = 0.0
            best_source = None
            best_query = None
            for query in queries:
                name = str(query.get("candidate_name") or "")
                score = _score(name, label)
                if name and (name.lower() in label.lower() or label.lower() in name.lower()):
                    score = max(score, 0.9)
                score = min(1.0, score * (0.85 + float(query.get("confidence", 0.5)) * 0.15))
                if score > best_score:
                    best_score = score
                    best_source = query.get("source")
                    best_query = name
            if best_score >= 0.42:
                candidates.append({**row, "score": round(best_score, 2), "source": best_source, "matched_text": best_query})
        if not rows and queries:
            for query in queries[:5]:
                name = str(query.get("candidate_name") or "")
                if name:
                    candidates.append({"name": name, label_field: name, "score": round(float(query.get("confidence", 0.5)), 2), "source": query.get("source"), "requires_selection": True})
        candidates = sorted(candidates, key=lambda item: item.get("score", 0), reverse=True)[:5]
        selected = candidates[0] if candidates and candidates[0].get("score", 0) >= 0.92 and not candidates[0].get("requires_selection") else None
        return {
            "matched": selected is not None,
            "selected": selected,
            "candidates": candidates,
            "warning": None if selected else f"{doctype} could not be confidently matched. Please select one of the candidates or search manually.",
        }


def _score(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _likely_name(text: str) -> str | None:
    candidates = extract_likely_supplier_names_from_header(text)
    if candidates:
        return str(candidates[0].get("candidate_name") or "")
    return None


def extract_likely_supplier_names_from_header(text: str) -> list[dict]:
    lines = normalize_ocr_lines(text)[:20]
    candidates: list[dict[str, Any]] = []
    buffer: list[str] = []
    for line in lines:
        lower = line.lower()
        if any(re.search(rf"\b{re.escape(label)}\b", lower) for label in BUYER_LABELS):
            break
        if _is_excluded(line):
            continue
        if _is_company_like(line):
            cleaned = _clean_company_name(line)
            if cleaned:
                buffer.append(cleaned)
                merged = _merge_company_lines(buffer)
                candidates.append({"candidate_name": merged, "source": "header", "confidence": _confidence(merged)})
        elif buffer:
            break
    deduped: dict[str, dict] = {}
    for candidate in candidates:
        name = candidate["candidate_name"]
        deduped[name.lower()] = max([deduped.get(name.lower(), candidate), candidate], key=lambda item: item["confidence"])
    return sorted(deduped.values(), key=lambda item: item["confidence"], reverse=True)[:5]


def _is_excluded(line: str) -> bool:
    normalized = re.sub(r"[^a-z0-9 ]+", "", line.lower()).strip()
    return normalized in SUPPLIER_EXCLUSION_LABELS or any(normalized.startswith(label) for label in SUPPLIER_EXCLUSION_LABELS)


def _is_company_like(line: str) -> bool:
    words = re.findall(r"[A-Za-z]{2,}", line)
    if len(words) < 2:
        return False
    lower = line.lower()
    uppercase_ratio = sum(1 for ch in line if ch.isupper()) / max(sum(1 for ch in line if ch.isalpha()), 1)
    return uppercase_ratio > 0.55 or any(word in lower for word in COMPANY_WORDS)


def _clean_company_name(line: str) -> str | None:
    cleaned = re.sub(r"\bA\s+Division\s+of\b.*", "", line, flags=re.I)
    cleaned = re.sub(r"\bCanitet\b.*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"\bSold\s+To\b.*", "", cleaned, flags=re.I)
    cleaned = re.sub(r"[^A-Za-z0-9 &.'/-]+", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" -")
    if not cleaned or _is_excluded(cleaned):
        return None
    return cleaned[:120]


def _merge_company_lines(lines: list[str]) -> str:
    if not lines:
        return ""
    if len(lines) == 1:
        return lines[0]
    combined = " ".join(lines[-2:])
    return combined[:120]


def _confidence(name: str) -> float:
    lower = name.lower()
    score = 0.55
    if any(word in lower for word in COMPANY_WORDS):
        score += 0.18
    if name.upper() == name and len(name) > 8:
        score += 0.12
    if len(name.split()) >= 3:
        score += 0.08
    return min(score, 0.85)
