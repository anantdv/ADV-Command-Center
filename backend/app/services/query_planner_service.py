from __future__ import annotations

import re
from datetime import date
from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.llm.extraction_service import LLMExtractionService
from app.llm.schemas import ExtractedIntent
from app.schemas.query_plan import QueryPlan
from app.utils.date_range_parser import parse_date_range_phrase
from app.utils.doctype_resolver import resolve_doctype
from app.utils.entity_extractor import extract_entity_filters, extract_record_name
from app.utils.field_alias_mapper import get_default_fields, map_field_alias
from app.utils.query_plan_validator import validate_query_plan
from app.utils.aggregation_planner import build_rule_based_aggregation_plan, detect_aggregation_intent
from app.utils.business_status_resolver import business_status_resolver

REPORT_ALIASES = {
    "stock balance": "Stock Balance",
    "stock ledger": "Stock Ledger",
    "general ledger": "General Ledger",
    "trial balance": "Trial Balance",
    "receivables": "Accounts Receivable",
    "receivable": "Accounts Receivable",
    "payables": "Accounts Payable",
    "payable": "Accounts Payable",
}

WRITE_WORDS = (
    "create", "add", "update", "change", "delete", "remove", "submit", "cancel",
    "approve", "reject", "make payment", "journal entry", "send email", "email customer",
)
SQL_PATTERN = re.compile(r"\b(select|insert|update|delete|drop|alter|truncate|union|from\s+tab)\b|;|--", re.IGNORECASE)


class QueryPlannerService:
    """Build safe, validated QueryPlan objects from flexible user language."""

    def __init__(self, extraction: LLMExtractionService | None = None):
        self.extraction = extraction or LLMExtractionService()

    async def plan(
        self,
        message: str,
        module_context: str | None = None,
        current_date: str | None = None,
        user: str = "unknown",
        conversation_id: str | None = None,
        extracted_intent: ExtractedIntent | None = None,
    ) -> QueryPlan:
        await self._audit("query_plan_started", message, user, conversation_id)
        text = " ".join(message.lower().split())
        if SQL_PATTERN.search(message):
            plan = QueryPlan(intent="unsupported", operation="none", confidence=1.0, blocked_reason="SQL-like query content is not allowed.")
            await self._audit("query_plan_failed", message, user, conversation_id, plan)
            return plan
        if self._write_requested(text):
            plan = QueryPlan(intent="blocked_write", operation="blocked", confidence=0.99, blocked_reason="Write operations require a controlled workflow.")
            await self._audit("query_plan_created", message, user, conversation_id, plan)
            return plan

        llm_plan: QueryPlan | None = None
        extracted = extracted_intent
        if extracted is None:
            extracted = await self.extraction.extract_intent(message, module_context, current_date, user, conversation_id)
        if extracted and extracted.confidence >= settings.llm_confidence_threshold:
            llm_plan = QueryPlan(
                intent=extracted.intent,
                operation=_operation(extracted.operation),
                doctype=extracted.doctype,
                report_name=extracted.report_name,
                record_name=extracted.record_name,
                filters=extracted.filters or {},
                fields=extracted.fields or [],
                date_range=extracted.date_range,
                limit=extracted.limit or 50,
                data=extracted.data or {},
                file_format=extracted.file_format,
                widget_type=extracted.widget_type,
                confidence=extracted.confidence,
                missing_information=extracted.missing_information,
                blocked_reason=extracted.blocked_reason,
                user_facing_summary=extracted.user_facing_summary,
                extraction_method="vertex_gemini",
            )

        fallback = self._fallback_plan(_apply_module_context(message, module_context), current_date)
        plan = self._merge(llm_plan, fallback, message)
        plan = validate_query_plan(plan)
        aggregation = build_rule_based_aggregation_plan(message, plan)
        if aggregation:
            plan.aggregation = aggregation
            plan.expects_aggregation = True
            plan.expects_chart = aggregation.chart_type != "table"
            plan.fields = aggregation.fields
            plan.normalized_filters = aggregation.normalized_filters
        await self._audit("query_filter_normalized", message, user, conversation_id, plan)
        await self._audit("query_plan_created", message, user, conversation_id, plan)
        return plan

    def _fallback_plan(self, message: str, current_date: str | None = None) -> QueryPlan:
        text = " ".join(message.lower().split())
        report_name = _match_alias(text, REPORT_ALIASES)
        if report_name:
            return QueryPlan(intent="run_report", operation="read", report_name=report_name, filters={}, confidence=0.9, extraction_method="rules")

        doctype = resolve_doctype(message)
        if not doctype and detect_aggregation_intent(message):
            text = " ".join(message.lower().split())
            if "sales" in text:
                doctype = "Sales Invoice"
            elif "purchase" in text:
                doctype = "Purchase Invoice"
        if not doctype:
            return QueryPlan(
                intent="unsupported",
                operation="none",
                confidence=0.2,
                missing_information=["doctype"],
                user_facing_summary="I could not identify which ERPNext document you want to search.",
                extraction_method="rules",
            )

        filters: dict[str, Any] = {}
        filters.update(_status_filters(text, doctype))
        filters.update(_value_filters(text))
        filters.update(extract_entity_filters(message, doctype))
        date_range = parse_date_range_phrase(text, _date_from_iso(current_date))
        record_name = extract_record_name(message, doctype)
        intent = "get_record" if record_name else "list_records"
        if record_name:
            filters = {}
        return QueryPlan(
            intent=intent,
            operation="read",
            doctype=doctype,
            record_name=record_name,
            filters=filters,
            fields=get_default_fields(doctype),
            date_range=date_range,
            limit=50,
            confidence=0.9,
            extraction_method="rules",
        )

    def _merge(self, llm_plan: QueryPlan | None, fallback: QueryPlan, message: str) -> QueryPlan:
        if not llm_plan or llm_plan.intent == "unsupported" or llm_plan.confidence < settings.llm_confidence_threshold:
            if llm_plan:
                fallback.extraction_method = "hybrid"
            return fallback

        # Deterministic extraction is authoritative for DocType aliases and
        # concrete filters because it is easier to test and cannot hallucinate.
        doctype = resolve_doctype(message, llm_plan.doctype) or fallback.doctype
        llm_plan.doctype = doctype
        if doctype:
            merged_filters = dict(llm_plan.filters or {})
            merged_filters.update(_status_filters(message.lower(), doctype))
            merged_filters.update(_value_filters(message.lower()))
            merged_filters.update(extract_entity_filters(message, doctype))
            llm_plan.filters = {map_field_alias(doctype, key): value for key, value in merged_filters.items()}
            llm_plan.fields = llm_plan.fields or get_default_fields(doctype)
            if llm_plan.date_range and llm_plan.date_range.get("period") and fallback.date_range:
                llm_plan.date_range = fallback.date_range
            else:
                llm_plan.date_range = llm_plan.date_range or fallback.date_range
            llm_plan.record_name = llm_plan.record_name or fallback.record_name
            llm_plan.intent = "get_record" if llm_plan.record_name else ("list_records" if llm_plan.intent in {"unsupported", "summary_query"} else llm_plan.intent)
        llm_plan.extraction_method = "hybrid"
        return llm_plan

    @staticmethod
    def _write_requested(text: str) -> bool:
        return any(re.search(rf"\b{re.escape(word)}\b", text) for word in WRITE_WORDS)

    @staticmethod
    async def _audit(action: str, message: str, user: str, conversation_id: str | None, plan: QueryPlan | None = None) -> None:
        await log_audit_event(AuditEvent(
            user=user,
            conversation_id=conversation_id,
            action=action,
            agent_name="query_planner",
            allowed=action not in {"query_plan_failed", "query_filter_normalization_failed"},
            risk_level="low",
            intent=plan.intent if plan else None,
            doctype=plan.doctype if plan else None,
            report_name=plan.report_name if plan else None,
            filters=plan.normalized_filters if plan else {},
            extraction_method=plan.extraction_method if plan else None,
            confidence=plan.confidence if plan else None,
            input_summary=_hashish(message),
            erp_data_sent=False,
        ))


def _operation(value: str) -> str:
    return value if value in {"read", "create", "update", "export", "pin", "blocked", "none"} else "none"


def _match_alias(text: str, aliases: dict[str, str]) -> str | None:
    for alias, target in sorted(aliases.items(), key=lambda item: len(item[0]), reverse=True):
        if re.search(rf"\b{re.escape(alias)}\b", text):
            return target
    return None


def _status_filters(text: str, doctype: str) -> dict[str, Any]:
    term = business_status_resolver.detect_term(text, doctype)
    resolved = business_status_resolver.resolve(doctype, term)
    if resolved:
        return resolved
    if doctype == "Item" and "disabled" in text:
        return {"disabled": 1}
    if doctype == "Customer" and "active" in text:
        return {"disabled": 0}
    return {}


def _value_filters(text: str) -> dict[str, Any]:
    between = re.search(r"\b(?:valued|value|amount|total)?\s*(?:between|from)\s+([\d,]+(?:\.\d+)?)\s+(?:to|and|-)\s+([\d,]+(?:\.\d+)?)\b", text)
    if between:
        return {"value": {"between": [_num(between.group(1)), _num(between.group(2))]}}
    above = re.search(r"\b(?:above|over|greater than|more than)\s+([\d,]+(?:\.\d+)?)\b", text)
    if above:
        return {"amount": {"operator": ">", "value": _num(above.group(1))}}
    below = re.search(r"\b(?:below|under|less than)\s+([\d,]+(?:\.\d+)?)\b", text)
    if below:
        return {"amount": {"operator": "<", "value": _num(below.group(1))}}
    return {}


def _num(value: str) -> float:
    number = float(value.replace(",", ""))
    return int(number) if number.is_integer() else number


def _date_from_iso(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _hashish(value: str) -> str:
    return f"message_len={len(value)}"


def _apply_module_context(message: str, module_context: str | None) -> str:
    if not module_context:
        return message
    context = module_context.strip().lower()
    rewrites = {
        "selling": [(r"\binvoices?\b", "sales invoices"), (r"\borders?\b", "sales orders"), (r"\bparties\b", "customers")],
        "buying": [(r"\binvoices?\b", "purchase invoices"), (r"\borders?\b", "purchase orders"), (r"\bparties\b", "suppliers"), (r"\breceipts?\b", "purchase receipts"), (r"\bquotations?\b", "supplier quotations")],
        "stock": [(r"\bentries\b", "stock entries"), (r"\bwarehouses?\b", "warehouses"), (r"\bbalance\b", "stock balance"), (r"\bmovement\b", "stock ledger"), (r"\brequests?\b", "material requests")],
        "accounts": [(r"\breceivables?\b", "accounts receivable"), (r"\bpayables?\b", "accounts payable"), (r"\bledger\b", "general ledger"), (r"\bpayments?\b", "payment entries"), (r"\bjournal\b", "journal entries")],
        "crm": [(r"\bleads?\b", "leads"), (r"\bopportunities\b", "opportunities"), (r"\bpipeline\b", "opportunities")],
        "projects": [(r"\bprojects?\b", "projects"), (r"\btasks?\b", "tasks"), (r"\btimesheets?\b", "timesheets")],
        "support": [(r"\btickets?\b", "issues"), (r"\bissues?\b", "issues"), (r"\bsla\b", "service level agreement")],
        "hr": [(r"\bemployees?\b", "employees"), (r"\battendance\b", "attendance"), (r"\bleave\b", "leave applications"), (r"\bsalary\b", "salary slips"), (r"\bexpense\b", "expense claims")],
        "assets": [(r"\bassets?\b", "assets"), (r"\bmovement\b", "asset movement"), (r"\bmaintenance\b", "asset maintenance"), (r"\brepair\b", "asset repair")],
        "manufacturing": [(r"\bwork orders?\b", "work orders"), (r"\bbom\b", "BOM"), (r"\bproduction plans?\b", "production plans"), (r"\bjob cards?\b", "job cards")],
    }
    key = {"accounting": "accounts", "purchase": "buying", "inventory": "stock", "helpdesk": "support"}.get(context, context)
    output = message
    for pattern, replacement in rewrites.get(key, []):
        output = re.sub(pattern, replacement, output, flags=re.IGNORECASE)
    return output
