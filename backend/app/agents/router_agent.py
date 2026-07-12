import re
from datetime import date
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.agents.runtime import AgentContext, AgentResult
from app.utils.field_mapper import ALLOWED_CREATE_FIELDS, ALLOWED_UPDATE_FIELDS
from app.utils.payload_builder import PayloadBuilder
from app.utils.date_range_parser import parse_date_range_phrase
from app.utils.workflow_intent_parser import parse_workflow_intent
from app.utils.detail_intent_parser import parse_detail_intent
from app.config import settings
from app.llm.extraction_service import LLMExtractionService
from app.llm.schemas import ExtractedIntent
from app.core.audit import AuditEvent, log_audit_event
from app.schemas.query_plan import QueryPlan
from app.schemas.aggregation import AggregationPlan
from app.schemas.report_composer import ReportComposerPlan
from app.services.query_planner_service import QueryPlannerService
from app.utils.report_composer_planner import ReportComposerPlanner

DOCTYPE_ALIASES = {
    "support ticket": "Issue",
    "issues": "Issue",
    "issue": "Issue",
    "purchase invoices": "Purchase Invoice",
    "purchase invoice": "Purchase Invoice",
    "sales invoices": "Sales Invoice",
    "sales invoice": "Sales Invoice",
    "purchase orders": "Purchase Order",
    "purchase order": "Purchase Order",
    "delivery notes": "Delivery Note",
    "delivery note": "Delivery Note",
    "delivery document": "Delivery Note",
    "purchase receipts": "Purchase Receipt",
    "purchase receipt": "Purchase Receipt",
    "goods receipt": "Purchase Receipt",
    "material requests": "Material Request",
    "material request": "Material Request",
    "sales orders": "Sales Order",
    "sales order": "Sales Order",
    "stock items": "Item",
    "stock item": "Item",
    "opportunities": "Opportunity",
    "opportunity": "Opportunity",
    "quotations": "Quotation",
    "quotation": "Quotation",
    "customers": "Customer",
    "customer": "Customer",
    "suppliers": "Supplier",
    "supplier": "Supplier",
    "employees": "Employee",
    "employee": "Employee",
    "projects": "Project",
    "project": "Project",
    "invoices": "Sales Invoice",
    "invoice": "Sales Invoice",
    "items": "Item",
    "item": "Item",
    "leads": "Lead",
    "lead": "Lead",
    "tasks": "Task",
    "task": "Task",
}

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

BLOCKED_WRITE_PHRASES = ("submit", "cancel", "delete", "remove", "amend", "approve", "reject", "make payment", "payment entry", "journal entry", "salary", "payroll", "bulk update", "send email", "email customer")

RECORD_ID_PATTERN = re.compile(
    r"\b(?:ACC-SINV|SINV|PINV|SAL-ORD|PUR-ORD|SAL-QTN|ITEM|CUST|SUPP)-[A-Z0-9-]+\b",
    re.IGNORECASE,
)


class IntentResult(BaseModel):
    intent: Literal[
        "list_records", "get_record", "run_report", "summary_query", "chart_query",
        "generate_file", "pin_to_dashboard", "crud_create", "crud_update", "workflow_list_pending", "workflow_get_detail", "workflow_apply_action", "report_composer", "blocked_write", "unsupported", "write_blocked",
    ]
    doctype: str | None = None
    report_name: str | None = None
    record_name: str | None = None
    filters: dict[str, Any] | None = None
    fields: list[str] | None = None
    limit: int = Field(20, ge=1, le=500)
    confidence: float = 0.7
    write_requested: bool = False
    raw_prompt: str = ""
    conversation_id: str | None = None
    sensitive_intent: bool = False
    file_format: Literal["xlsx", "csv", "pdf", "html", "png"] | None = None
    source_type: Literal["doctype", "report", "chat_result"] | None = None
    source_name: str | None = None
    rows: list[dict[str, Any]] | None = None
    chart_config: dict[str, Any] | None = None
    operation: Literal["create", "update"] | None = None
    data: dict[str, Any] | None = None
    missing_info_hint: str | None = None
    date_range: dict[str, str] | None = None
    widget_type: Literal["kpi", "line_chart", "bar_chart", "pie_chart", "donut_chart", "area_chart", "table", "summary_card"] | None = None
    extraction_method: Literal["vertex_gemini", "rules"] = "rules"
    llm_provider: str | None = None
    llm_model: str | None = None
    llm_confidence: float | None = None
    privacy_checked: bool = False
    privacy_allowed: bool = False
    erp_data_sent: bool = False
    fallback_used: bool = False
    query_plan: QueryPlan | None = None
    aggregation: AggregationPlan | None = None
    report_composer_plan: ReportComposerPlan | None = None


class RouterAgent:
    def __init__(self, extraction: LLMExtractionService | None = None, query_planner: QueryPlannerService | None = None):
        self.extraction = extraction or LLMExtractionService()
        self.query_planner = query_planner or QueryPlannerService(self.extraction)

    async def classify(self, message: str, module_context: str | None = None, user: str = "unknown", conversation_id: str | None = None, date_range_context: dict[str, str] | None = None) -> IntentResult:
        text = " ".join(message.lower().split())
        workflow = parse_workflow_intent(message)
        if workflow:
            data = {"action": workflow.get("action")} if workflow.get("action") else None
            if module_context and module_context.lower() == "selling" and workflow["intent"] == "workflow_list_pending" and not workflow.get("doctype"):
                data = {"doctypes": ["Quotation", "Sales Order", "Sales Invoice", "Delivery Note"]}
            return IntentResult(intent=workflow["intent"], doctype=workflow.get("doctype"), record_name=workflow.get("record_name"), data=data, confidence=0.96, raw_prompt=message, date_range=date_range_context)
        if self._blocked_write_requested(text):
            return IntentResult(intent="blocked_write", write_requested=True, confidence=0.99, raw_prompt=message, date_range=date_range_context)
        detail = parse_detail_intent(message)
        if detail.matched:
            return IntentResult(intent="get_record", doctype=detail.doctype, record_name=detail.name, confidence=detail.confidence, raw_prompt=message, missing_info_hint="I found the document number, but I need the document type to open it." if detail.needs_doctype else None, date_range=date_range_context)
        if settings.enable_report_composer and ReportComposerPlanner.looks_like_report_prompt(message):
            plan = await ReportComposerPlanner().plan_from_message(message, module_context)
            return IntentResult(intent="report_composer", doctype=plan.source.source_name, confidence=plan.confidence, raw_prompt=message, report_composer_plan=plan, date_range=plan.date_range or date_range_context)
        file_format = self._file_format(text)
        file_requested = bool(file_format and any(term in text for term in ("export", "generate", "create", "save", "download")))
        controlled_crud_requested = bool(re.search(r"\b(create|add|update|change)\b", text))
        if (file_requested or controlled_crud_requested) and not settings.enable_llm_extraction:
            return self._with_date_context(await self._classify_rules(message, module_context), message, date_range_context)
        extracted = await self.extraction.extract_intent(message, module_context, user=user, conversation_id=conversation_id)
        if extracted and extracted.intent == "blocked_write":
            await self._audit_routing("llm_blocked_write_detected", extracted, user, conversation_id)
            return self._with_date_context(self._from_extracted(extracted, message), message, date_range_context)
        if extracted and extracted.intent in {"generate_file", "pin_to_dashboard", "crud_create", "crud_update"} and extracted.confidence >= settings.llm_confidence_threshold:
            return self._with_date_context(self._from_extracted(extracted, message), message, date_range_context)
        if extracted:
            await self._audit_routing("llm_extraction_fallback_to_rules", extracted, user, conversation_id, fallback=True)
        if file_requested or controlled_crud_requested:
            return self._with_date_context(await self._classify_rules(message, module_context), message, date_range_context)
        plan = await self.query_planner.plan(message, module_context, user=user, conversation_id=conversation_id, extracted_intent=extracted)
        if plan.intent != "unsupported":
            return self._with_date_context(self._from_query_plan(plan, message, bool(extracted)), message, date_range_context)
        result = await self._classify_rules(message, module_context)
        result.extraction_method = "rules"
        result.fallback_used = bool(extracted)
        return self._with_date_context(result, message, date_range_context)

    @staticmethod
    def _with_date_context(intent: IntentResult, message: str, date_range_context: dict[str, str] | None) -> IntentResult:
        if date_range_context and not intent.date_range and not parse_date_range_phrase(message):
            intent.date_range = date_range_context
        return intent

    @staticmethod
    async def _audit_routing(action: str, extracted: ExtractedIntent, user: str, conversation_id: str | None, fallback: bool = False) -> None:
        await log_audit_event(AuditEvent(
            user=user,
            conversation_id=conversation_id,
            action=action,
            agent_name="router_agent",
            allowed=action != "llm_blocked_write_detected",
            risk_level="high" if action == "llm_blocked_write_detected" else "low",
            intent=extracted.intent,
            operation=extracted.operation,
            doctype=extracted.doctype,
            report_name=extracted.report_name,
            provider=extracted.provider,
            model=extracted.model,
            confidence=extracted.confidence,
            fallback_used=fallback,
            privacy_allowed=extracted.privacy_allowed,
            erp_data_sent=False,
        ))

    async def _classify_rules(self, message: str, module_context: str | None = None) -> IntentResult:
        text = " ".join(message.lower().split())
        if module_context and module_context.lower() == "selling":
            if re.search(r"\bshow\s+(?:my\s+)?(?:invoices|invoice)\b", text):
                text = text.replace("invoices", "sales invoices").replace("invoice", "sales invoice")
            if re.search(r"\bshow\s+(?:my\s+)?(?:orders|order)\b", text):
                text = text.replace("orders", "sales orders").replace("order", "sales order")
            if re.search(r"\bparties\b", text):
                text = text.replace("parties", "customers")
            if re.search(r"\btop customers\b", text):
                return IntentResult(intent="chart_query", doctype="Sales Invoice", fields=["customer", "grand_total"], limit=500, confidence=.94, raw_prompt=message, filters={})
        file_format = self._file_format(text)
        file_requested = bool(file_format and any(term in text for term in ("export", "generate", "create", "save", "download")))
        if file_requested:
            report_name = self._match_alias(text, REPORT_ALIASES)
            doctype = self._match_alias(text, DOCTYPE_ALIASES)
            source_type: Literal["doctype", "report", "chat_result"] = "report" if report_name else ("doctype" if doctype else "chat_result")
            source_name = report_name or doctype or "Previous chat result"
            return IntentResult(intent="generate_file", report_name=report_name, doctype=doctype, filters=self._filters(text, doctype) if doctype else {}, confidence=.97, raw_prompt=message, file_format=file_format, source_type=source_type, source_name=source_name)
        # A support ticket may legitimately describe a blocked ERP operation
        # (for example, "user cannot submit invoice"). Treat the outer action
        # as safe Issue creation; the quoted problem text is only its content.
        if re.search(r"\b(?:create|add)\s+(?:a\s+)?(?:support ticket|issue)\b", text):
            return IntentResult(intent="crud_create", operation="create", doctype="Issue", data=PayloadBuilder.extract_create("Issue", message), confidence=.97, raw_prompt=message)
        if self._blocked_write_requested(text):
            return IntentResult(
                intent="blocked_write",
                write_requested=True,
                confidence=0.99,
                raw_prompt=message,
            )

        create_requested = bool(re.search(r"\b(create|add)\b", text))
        update_requested = bool(re.search(r"\b(update|change)\b", text))
        if create_requested or update_requested:
            doctype = self._match_alias(text, DOCTYPE_ALIASES)
            operation: Literal["create", "update"] = "create" if create_requested else "update"
            supported = ALLOWED_CREATE_FIELDS if operation == "create" else ALLOWED_UPDATE_FIELDS
            if not doctype or doctype not in supported:
                return IntentResult(intent="blocked_write", write_requested=True, doctype=doctype, operation=operation, confidence=.98, raw_prompt=message)
            if operation == "create":
                data = PayloadBuilder.extract_create(doctype, message)
                return IntentResult(intent="crud_create", operation="create", doctype=doctype, data=data, confidence=.94, raw_prompt=message)
            record_name, data = PayloadBuilder.extract_update(doctype, message)
            return IntentResult(intent="crud_update", operation="update", doctype=doctype, record_name=record_name, data=data, missing_info_hint=None if record_name and data else "Include the record name, field, and new value.", confidence=.92, raw_prompt=message)

        report_name = self._match_alias(text, REPORT_ALIASES)
        if report_name:
            return IntentResult(
                intent="run_report",
                report_name=report_name,
                filters={},
                confidence=0.95,
                raw_prompt=message,
            )

        doctype = self._match_alias(text, DOCTYPE_ALIASES)
        if not doctype:
            return IntentResult(intent="unsupported", confidence=0.2, raw_prompt=message)

        filters = self._filters(text, doctype)
        date_range = parse_date_range_phrase(text)
        filters = {**filters, **self._value_filters(text)}
        record_name = self._record_name(text, doctype)
        if record_name:
            return IntentResult(
                intent="get_record",
                doctype=doctype,
                record_name=record_name,
                filters=filters,
                date_range=date_range,
                confidence=0.94,
                raw_prompt=message,
            )

        intent = "chart_query" if any(word in text for word in ("chart", "graph", "trend")) else "list_records"
        return IntentResult(
            intent=intent,
            doctype=doctype,
            filters=filters,
            date_range=date_range,
            confidence=0.9,
            raw_prompt=message,
        )

    @classmethod
    def _from_extracted(cls, extracted: ExtractedIntent, message: str) -> IntentResult:
        filters=dict(extracted.filters or {})
        if extracted.date_range and extracted.doctype:
            field={"Sales Invoice":"posting_date","Purchase Invoice":"posting_date","Sales Order":"transaction_date","Purchase Order":"transaction_date","Quotation":"transaction_date","Lead":"creation","Opportunity":"transaction_date","Issue":"opening_date"}.get(extracted.doctype)
            if field:
                start=extracted.date_range.get("from_date");end=extracted.date_range.get("to_date")
                if extracted.date_range.get("period") == "this_month":
                    today=date.today();start=today.replace(day=1).isoformat();end=today.isoformat()
                if start and end: filters[field]=["between",[start,end]]
        if extracted.date_range and extracted.report_name:
            for key in ("from_date", "to_date"):
                if extracted.date_range.get(key): filters[key]=extracted.date_range[key]
        source_type = "report" if extracted.report_name else ("doctype" if extracted.doctype else "chat_result")
        source_name = extracted.report_name or extracted.doctype or "Previous chat result"
        return IntentResult(intent=extracted.intent,operation=extracted.operation if extracted.operation in {"create","update"} else None,doctype=extracted.doctype,report_name=extracted.report_name,record_name=extracted.record_name,data=extracted.data,filters=filters,fields=extracted.fields or None,limit=extracted.limit,confidence=extracted.confidence,write_requested=extracted.intent=="blocked_write",raw_prompt=message,file_format=extracted.file_format,source_type=source_type if extracted.intent=="generate_file" else None,source_name=source_name if extracted.intent=="generate_file" else None,date_range=extracted.date_range,widget_type=extracted.widget_type,extraction_method="vertex_gemini",llm_provider=extracted.provider or "vertex_gemini",llm_model=extracted.model,llm_confidence=extracted.confidence,privacy_checked=extracted.privacy_checked,privacy_allowed=extracted.privacy_allowed,erp_data_sent=False,fallback_used=extracted.fallback_used)

    @staticmethod
    def _from_query_plan(plan: QueryPlan, message: str, fallback_used: bool = False) -> IntentResult:
        source_type = "report" if plan.report_name else ("doctype" if plan.doctype else "chat_result")
        source_name = plan.report_name or plan.doctype or "Previous chat result"
        operation = plan.operation if plan.operation in {"create", "update"} else None
        return IntentResult(
            intent=plan.intent if plan.intent != "blocked_write" else "blocked_write",
            operation=operation,
            doctype=plan.doctype,
            report_name=plan.report_name,
            record_name=plan.record_name,
            data=plan.data or None,
            filters=plan.normalized_filters or plan.filters or {},
            fields=plan.fields or None,
            limit=plan.limit,
            confidence=plan.confidence,
            write_requested=plan.intent == "blocked_write",
            raw_prompt=message,
            file_format=plan.file_format,
            source_type=source_type if plan.intent == "generate_file" else None,
            source_name=source_name if plan.intent == "generate_file" else None,
            date_range=None if plan.normalized_filters else plan.date_range,
            widget_type=plan.widget_type,
            extraction_method="rules" if plan.extraction_method == "rules" else "vertex_gemini",
            llm_confidence=plan.confidence if plan.extraction_method != "rules" else None,
            privacy_checked=plan.extraction_method != "rules",
            privacy_allowed=plan.extraction_method != "rules",
            erp_data_sent=False,
            fallback_used=fallback_used or plan.extraction_method == "hybrid",
            query_plan=plan,
            aggregation=plan.aggregation,
        )

    async def handle(self, context: AgentContext) -> AgentResult:
        intent = await self.classify(context.message)
        return AgentResult(
            agent_name="router_agent",
            content=f"Classified as {intent.intent}",
            data=intent.model_dump(),
        )

    @staticmethod
    def _match_alias(text: str, aliases: dict[str, str]) -> str | None:
        for alias, target in aliases.items():
            if re.search(rf"\b{re.escape(alias)}\b", text):
                return target
        return None

    @staticmethod
    def _file_format(text: str) -> Literal["xlsx", "csv", "pdf", "html", "png"] | None:
        if re.search(r"\b(excel|xlsx)\b", text): return "xlsx"
        if re.search(r"\bcsv\b", text): return "csv"
        if re.search(r"\bpdf\b", text): return "pdf"
        if re.search(r"\bhtml\b", text): return "html"
        if re.search(r"\b(png|chart image|image)\b", text): return "png"
        if "save this chart" in text: return "png"
        return None

    @staticmethod
    def _blocked_write_requested(text: str) -> bool:
        command_patterns = (
            r"^(?:please\s+)?(?:submit|cancel|delete|remove|amend|approve|reject)\b",
            r"^(?:please\s+)?(?:create|make)\s+(?:a\s+)?(?:payment entry|journal entry|salary|payroll)\b",
            r"^(?:please\s+)?bulk\s+update\b",
            r"^(?:please\s+)?(?:send\s+email|email\s+customer)\b",
        )
        return any(re.search(pattern, text) for pattern in command_patterns)

    @staticmethod
    def _filters(text: str, doctype: str) -> dict[str, Any]:
        if doctype in {"Sales Invoice", "Purchase Invoice"}:
            if "overdue" in text:
                return {"status": "Overdue"}
            if "unpaid" in text:
                return {"status": "unpaid"}
            if "paid" in text:
                return {"outstanding_amount": ["=", 0]}
            if "draft" in text:
                return {"docstatus": 0}
            if "submitted" in text:
                return {"docstatus": 1}
        if doctype in {"Sales Order", "Purchase Order"}:
            if "open" in text:
                return {"status": ["not in", ["Closed", "Completed", "Cancelled"]]}
            if "closed" in text:
                return {"status": "Closed"}
        if doctype == "Item" and "disabled" in text:
            return {"disabled": 1}
        if doctype == "Customer" and "active" in text:
            return {"disabled": 0}
        return {}

    @staticmethod
    def _value_filters(text: str) -> dict[str, Any]:
        between = re.search(r"\b(?:valued|value|amount|total)?\s*(?:between|from)\s+([\d,]+(?:\.\d+)?)\s+(?:to|and|-)\s+([\d,]+(?:\.\d+)?)\b", text)
        if between:
            return {"value": ["between", [_num(between.group(1)), _num(between.group(2))]]}
        above = re.search(r"\b(?:above|over|greater than|more than)\s+([\d,]+(?:\.\d+)?)\b", text)
        if above:
            return {"value": [">", _num(above.group(1))]}
        below = re.search(r"\b(?:below|under|less than)\s+([\d,]+(?:\.\d+)?)\b", text)
        if below:
            return {"value": ["<", _num(below.group(1))]}
        return {}

    @staticmethod
    def _record_name(text: str, doctype: str) -> str | None:
        known = RECORD_ID_PATTERN.search(text)
        if known:
            return known.group(0).upper()
        singular = {
            "Customer": "customer",
            "Supplier": "supplier",
            "Item": "item",
            "Sales Invoice": "invoice",
        }.get(doctype)
        if singular:
            match = re.search(rf"\b(?:show|get|find)\s+{singular}\s+([^\s,?]+)", text, re.IGNORECASE)
            if match and match.group(1).lower() not in {"list", "records", "details"}:
                return match.group(1).upper()
        return None


def _num(value: str) -> float:
    return float(value.replace(",", ""))
