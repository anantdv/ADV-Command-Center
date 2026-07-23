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
from app.schemas.command_intent import CommandIntent
from app.services.command_router_service import command_router_service
from app.llm.extraction_service import LLMExtractionService
from app.llm.schemas import ExtractedIntent
from app.core.audit import AuditEvent, log_audit_event
from app.schemas.query_plan import QueryPlan
from app.schemas.aggregation import AggregationPlan
from app.schemas.report_composer import ReportComposerPlan
from app.services.query_planner_service import QueryPlannerService
from app.utils.report_composer_planner import ReportComposerPlanner
from app.utils.business_status_resolver import business_status_resolver

DOCTYPE_ALIASES = {
    "support ticket": "Issue",
    "issues": "Issue",
    "issue": "Issue",
    "purchase invoices": "Purchase Invoice",
    "purchase invoice": "Purchase Invoice",
    "sales invoices": "Sales Invoice",
    "sales invoice": "Sales Invoice",
    "si": "Sales Invoice",
    "s i": "Sales Invoice",
    "purchase orders": "Purchase Order",
    "purchase order": "Purchase Order",
    "po": "Purchase Order",
    "p o": "Purchase Order",
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
    "stock entries": "Stock Entry",
    "stock entry": "Stock Entry",
    "material transfer": "Stock Entry",
    "material transfers": "Stock Entry",
    "journal entries": "Journal Entry",
    "journal entry": "Journal Entry",
    "payment entries": "Payment Entry",
    "payment entry": "Payment Entry",
    "expense claims": "Expense Claim",
    "expense claim": "Expense Claim",
    "leave applications": "Leave Application",
    "leave application": "Leave Application",
    "assets": "Asset",
    "asset": "Asset",
    "work orders": "Work Order",
    "work order": "Work Order",
    "job cards": "Job Card",
    "job card": "Job Card",
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
        "run_analytics", "generate_chart", "generate_file", "pin_to_dashboard", "crud_create", "crud_update", "workflow_list_pending", "workflow_get_detail", "workflow_apply_action", "report_composer", "visualize_existing_report", "regroup_existing_report", "export_existing_report", "pin_existing_report", "clarification_required", "blocked_write", "unsupported", "write_blocked",
    ]
    doctype: str | None = None
    report_name: str | None = None
    analytics_key: str | None = None
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
        if self._report_ui_action_without_context(text):
            return IntentResult(
                intent="unsupported",
                confidence=0.95,
                raw_prompt=message,
                missing_info_hint="Please select a chart or report result first, then choose that action from the result buttons.",
                date_range=date_range_context,
            )
        planned_create = self._planned_create_intent(message)
        if planned_create:
            return self._with_date_context(planned_create, message, date_range_context)
        if self._blocked_write_requested(text):
            return IntentResult(intent="blocked_write", write_requested=True, confidence=0.99, raw_prompt=message, date_range=date_range_context)

        detail = parse_detail_intent(message)
        if detail.matched:
            return IntentResult(intent="get_record", doctype=detail.doctype, record_name=detail.name, confidence=detail.confidence, raw_prompt=message, missing_info_hint="I found the document number, but I need the document type to open it." if detail.needs_doctype else None, date_range=date_range_context)

        command_intent = await command_router_service.route(message, module_context, date_range_context)
        if command_intent.intent != "unsupported":
            return self._from_command_intent(command_intent)

        if settings.enable_report_composer and ReportComposerPlanner.looks_like_report_prompt(message):
            plan = await ReportComposerPlanner().plan_from_message(message, module_context)
            return IntentResult(intent="report_composer", doctype=plan.source.source_name, confidence=plan.confidence, raw_prompt=message, report_composer_plan=plan, date_range=plan.date_range or date_range_context)
        file_format = self._file_format(text)
        if self._report_ui_action_without_context(text):
            return IntentResult(
                intent="unsupported",
                confidence=0.95,
                raw_prompt=message,
                missing_info_hint="Please select a chart or report result first, then choose that action from the result buttons.",
            )
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
        if date_range_context and not intent.date_range and not parse_date_range_phrase(message) and not re.search(r"\ball\b", message, re.I):
            intent.date_range = date_range_context
        return intent

    @staticmethod
    def _from_command_intent(command: CommandIntent) -> IntentResult:
        mapped_intent = {
            "get_record_detail": "get_record",
            "crud_create_draft": "crud_create",
            "crud_update_draft": "crud_update",
        }.get(command.intent, command.intent)
        data = dict(command.action_payload or {})
        if command.module_context and command.module_context.lower() == "selling" and command.intent == "workflow_list_pending" and not command.doctype:
            data.setdefault("doctypes", ["Quotation", "Sales Order", "Sales Invoice", "Delivery Note"])
        widget_type = None
        if command.chart_requested:
            widget_type = {
                "line": "line_chart",
                "bar": "bar_chart",
                "pie": "pie_chart",
                "donut": "donut_chart",
                "area": "area_chart",
            }.get(str(command.chart_type or "").lower())
        filters = dict(command.filters or {})
        if command.date_range and command.doctype:
            date_field = {
                "Sales Invoice": "posting_date",
                "Purchase Invoice": "posting_date",
                "Sales Order": "transaction_date",
                "Purchase Order": "transaction_date",
                "Quotation": "transaction_date",
                "Delivery Note": "posting_date",
                "Purchase Receipt": "posting_date",
                "Material Request": "transaction_date",
            }.get(command.doctype)
            if date_field and date_field not in filters and command.date_range.get("from_date") and command.date_range.get("to_date"):
                filters[date_field] = ["between", [command.date_range["from_date"], command.date_range["to_date"]]]
        return IntentResult(
            intent=mapped_intent,  # type: ignore[arg-type]
            doctype=command.doctype,
            report_name=command.report_name,
            analytics_key=command.analytics_key,
            record_name=command.record_name,
            filters=filters,
            fields=command.fields or None,
            limit=50 if mapped_intent in {"run_analytics", "generate_chart"} else 20,
            confidence=command.confidence,
            raw_prompt=command.message,
            date_range=command.date_range,
            operation="create" if command.intent == "crud_create_draft" else "update" if command.intent == "crud_update_draft" else None,
            data=data or None,
            missing_info_hint=", ".join(command.missing_information) if command.missing_information else None,
            chart_config={"chart_type": command.chart_type} if command.chart_requested else None,
            widget_type=widget_type,
            extraction_method="rules",
        )

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

        create_requested = bool(re.search(r"\b(create|add|draft|prepare|make|raise|enter)\b", text) or re.search(r"\bgenerate\s+(?:a\s+)?draft\b", text))
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
        if date_range:
            date_field = {
                "Sales Invoice": "posting_date",
                "Purchase Invoice": "posting_date",
                "Sales Order": "transaction_date",
                "Purchase Order": "transaction_date",
                "Quotation": "transaction_date",
                "Delivery Note": "posting_date",
                "Purchase Receipt": "posting_date",
                "Material Request": "transaction_date",
            }.get(doctype)
            if date_field and date_range.get("from_date") and date_range.get("to_date"):
                filters[date_field] = ["between", [date_range["from_date"], date_range["to_date"]]]
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

    @staticmethod
    def _planned_create_intent(message: str) -> IntentResult | None:
        text = " ".join(message.lower().split())
        explicit_create = bool(re.search(r"\b(create|add|draft|prepare|make|raise|enter)\b", text) or re.search(r"\bgenerate\s+(?:a\s+)?draft\b", text))
        implicit_transaction_create = bool(
            re.match(
                r"^(?:sales invoice|purchase invoice|sales order|purchase order|quotation|delivery note|purchase receipt|material request|stock entry)\b",
                text,
            )
            and not re.search(r"\b(show|list|open|view|get|find|report|chart|trend|summary)\b", text)
            and re.search(r"\b(for|with|item|items?|qty|quantity|price|rate|@|at)\b", text)
        )
        if not (explicit_create or implicit_transaction_create):
            return None
        doctype = RouterAgent._match_alias(text, DOCTYPE_ALIASES)
        if not doctype:
            return None
        if doctype not in ALLOWED_CREATE_FIELDS:
            return None
        data = PayloadBuilder.extract_create(doctype, message)
        return IntentResult(intent="crud_create", operation="create", doctype=doctype, data=data, confidence=.96, raw_prompt=message)

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
        filters = dict(plan.normalized_filters or plan.filters or {})
        if plan.date_range and plan.doctype:
            date_field = {
                "Sales Invoice": "posting_date",
                "Purchase Invoice": "posting_date",
                "Sales Order": "transaction_date",
                "Purchase Order": "transaction_date",
                "Quotation": "transaction_date",
                "Delivery Note": "posting_date",
                "Purchase Receipt": "posting_date",
                "Material Request": "transaction_date",
            }.get(plan.doctype)
            if date_field and date_field not in filters and plan.date_range.get("from_date") and plan.date_range.get("to_date"):
                filters[date_field] = ["between", [plan.date_range["from_date"], plan.date_range["to_date"]]]
        return IntentResult(
            intent=plan.intent if plan.intent != "blocked_write" else "blocked_write",
            operation=operation,
            doctype=plan.doctype,
            report_name=plan.report_name,
            record_name=plan.record_name,
            data=plan.data or None,
            filters=filters,
            fields=plan.fields or None,
            limit=plan.limit,
            confidence=plan.confidence,
            write_requested=plan.intent == "blocked_write",
            raw_prompt=message,
            file_format=plan.file_format,
            source_type=source_type if plan.intent == "generate_file" else None,
            source_name=source_name if plan.intent == "generate_file" else None,
            date_range=None if filters else plan.date_range,
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
    def _report_ui_action_without_context(text: str) -> bool:
        safe_ui_patterns = (
            r"\bchange\s+chart\s+type\b",
            r"\bchange\s+columns?\b",
            r"\brefine\s+filters?\b",
            r"\bsave\s+report\s+view\b",
            r"\bpin\s+(?:to\s+)?(?:overview|module)?\b",
            r"\bconvert\s+to\s+(?:bar|line|area|pie|donut)\s+chart\b",
        )
        return any(re.search(pattern, text) for pattern in safe_ui_patterns)

    @staticmethod
    def _filters(text: str, doctype: str) -> dict[str, Any]:
        status = business_status_resolver.resolve(doctype, business_status_resolver.detect_term(text, doctype))
        if status:
            return status
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
