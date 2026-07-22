from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.entity_resolution import EntityMatch, EntitySearchRequest, EntitySearchResponse
from app.services.erpnext_service import ERPNextService


AUTO_RESOLVE_SCORE = 0.95
AUTO_RESOLVE_GAP = 0.12
SUGGEST_SCORE = 0.65

ALLOWED_ENTITY_DOCTYPES = {
    "Supplier",
    "Customer",
    "Item",
    "Warehouse",
    "Company",
    "Cost Center",
    "Project",
    "Account",
    "Currency",
    "Territory",
    "Sales Person",
    "Employee",
    "Asset",
    "Batch",
    "Serial No",
    "Price List",
    "Purchase Taxes and Charges Template",
    "Sales Taxes and Charges Template",
}

SEARCH_FIELD_MAP: dict[str, list[str]] = {
    "Supplier": ["name", "supplier_name", "supplier_group", "disabled"],
    "Customer": ["name", "customer_name", "customer_group", "territory", "disabled"],
    "Item": ["name", "item_code", "item_name", "item_group", "stock_uom", "description", "disabled"],
    "Warehouse": ["name", "warehouse_name", "company", "disabled"],
    "Company": ["name", "company_name"],
    "Cost Center": ["name", "cost_center_name", "company", "disabled"],
    "Project": ["name", "project_name", "status"],
    "Account": ["name", "account_name", "account_number", "company", "disabled"],
    "Currency": ["name", "currency_name", "enabled"],
    "Employee": ["name", "employee_name", "department", "status"],
    "Asset": ["name", "asset_name", "item_code", "status"],
}

LABEL_FIELD = {
    "Supplier": "supplier_name",
    "Customer": "customer_name",
    "Item": "item_name",
    "Warehouse": "warehouse_name",
    "Company": "company_name",
    "Cost Center": "cost_center_name",
    "Project": "project_name",
    "Account": "account_name",
    "Currency": "currency_name",
    "Employee": "employee_name",
    "Asset": "asset_name",
}


class EntityResolutionService:
    """Resolve natural-language Link values to permission-filtered ERPNext records."""

    def __init__(self, erp: ERPNextService | None = None):
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))

    async def search(self, request: EntitySearchRequest, cookies: dict | None = None) -> EntitySearchResponse:
        doctype = request.doctype.strip()
        if doctype not in ALLOWED_ENTITY_DOCTYPES:
            return EntitySearchResponse(doctype=doctype, query=request.query, matches=[])
        query = _normalize_query(request.query)
        if not query or len(query) < 2:
            return EntitySearchResponse(doctype=doctype, query=request.query, matches=[])
        fields = SEARCH_FIELD_MAP.get(doctype, ["name"])
        try:
            rows = (await self.erp.list_records(doctype, {}, fields, 500, cookies=cookies)).records
        except Exception:
            rows = [{"name": item["name"], "label": item.get("label"), "description": item.get("description")} for item in await self.erp.search_link(doctype, request.query, cookies, 50)]
        scored = [self._score_row(doctype, request.query, row) for row in rows if not _disabled(row)]
        matches = [item for item in scored if item.score >= SUGGEST_SCORE or item.match_type.startswith("exact")]
        matches.sort(key=lambda item: item.score, reverse=True)
        return EntitySearchResponse(doctype=doctype, query=request.query, matches=matches[: request.limit], has_more=len(matches) > request.limit)

    def classify(self, matches: list[EntityMatch]) -> tuple[str, str | None]:
        if not matches:
            return "no_match", None
        top = matches[0]
        second = matches[1].score if len(matches) > 1 else 0
        if top.score >= AUTO_RESOLVE_SCORE and (top.score - second) >= AUTO_RESOLVE_GAP:
            return "resolved", top.value
        return "needs_selection", None

    @staticmethod
    def _score_row(doctype: str, query: str, row: dict[str, Any]) -> EntityMatch:
        name = str(row.get("name") or "")
        label_field = LABEL_FIELD.get(doctype, "label")
        label = str(row.get(label_field) or row.get("label") or name)
        description = str(row.get("description") or row.get("item_group") or row.get("supplier_group") or row.get("customer_group") or doctype)
        query_norm = _norm(query)
        candidates = [name, label, str(row.get("item_code") or ""), str(row.get("barcode") or "")]
        normalized = [_norm(value) for value in candidates if value]
        if query_norm in normalized:
            score, match_type = 1.0, "exact"
        elif any(value.startswith(query_norm) for value in normalized):
            score, match_type = 0.9, "prefix"
        elif any(query_norm in value for value in normalized):
            score, match_type = 0.82, "contains"
        else:
            haystack = " ".join(normalized)
            token_score = _token_score(query_norm, haystack)
            fuzzy = max([SequenceMatcher(None, query_norm, value).ratio() for value in normalized] or [0])
            score = max(token_score, fuzzy * 0.92)
            match_type = "name_tokens" if token_score >= fuzzy else "fuzzy"
        return EntityMatch(
            value=name,
            label=label,
            description=description,
            match_type=match_type,
            score=round(float(score), 4),
            disabled=_disabled(row),
            metadata={key: value for key, value in row.items() if key not in {"name", label_field, "label", "disabled"} and value not in (None, "")},
        )


def _normalize_query(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def _norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").lower()).strip()


def _token_score(query: str, haystack: str) -> float:
    q_tokens = [token for token in query.split() if token]
    h_tokens = set(haystack.split())
    if not q_tokens:
        return 0
    hits = sum(1 for token in q_tokens if token in h_tokens or any(part.startswith(token) for part in h_tokens))
    return hits / len(q_tokens) * 0.86


def _disabled(row: dict[str, Any]) -> bool:
    value = row.get("disabled")
    return value in {1, "1", True, "Yes", "yes"}


entity_resolution_service = EntityResolutionService()
