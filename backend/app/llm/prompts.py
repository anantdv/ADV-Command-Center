import json

ALLOWED_DOCTYPES = ["Customer", "Supplier", "Item", "Sales Invoice", "Purchase Invoice", "Sales Order", "Purchase Order", "Quotation", "Lead", "Opportunity", "Project", "Task", "Employee", "Issue"]
ALLOWED_CREATE_DOCTYPES = ["Customer", "Supplier", "Item", "Quotation", "Lead", "Opportunity", "Issue"]
ALLOWED_UPDATE_DOCTYPES = ["Customer", "Supplier", "Item", "Lead", "Opportunity", "Issue", "Quotation"]
ALLOWED_REPORTS = ["Stock Balance", "Stock Ledger", "General Ledger", "Trial Balance", "Accounts Receivable", "Accounts Payable"]
ALLOWED_FILE_FORMATS = ["xlsx", "csv", "pdf", "html", "png"]
ALLOWED_WIDGET_TYPES = ["kpi", "line_chart", "bar_chart", "pie_chart", "donut_chart", "area_chart", "table", "summary_card"]
BLOCKED_OPERATIONS = ["submit", "cancel", "delete", "remove", "amend", "approve", "reject", "payment entry", "journal entry", "payroll", "salary", "bulk update", "send email", "raw sql", "sql", "ignore permissions", "admin access", "administrator", "bypass permission", "api key", "api secret", "password", "token"]


def build_intent_extraction_system_prompt() -> str:
    return f"""You are the JSON-only intent extraction engine for ADV Command Center.
You do not execute ERPNext actions, decide permissions, call tools, or receive ERPNext records.
Return valid JSON only, with no markdown, explanations, or comments.
Allowed intents: list_records, get_record, run_report, generate_file, pin_to_dashboard, crud_create, crud_update, blocked_write, unsupported.
Allowed DocTypes: {', '.join(ALLOWED_DOCTYPES)}.
Allowed create DocTypes: {', '.join(ALLOWED_CREATE_DOCTYPES)}.
Allowed update DocTypes: {', '.join(ALLOWED_UPDATE_DOCTYPES)}.
Allowed reports: {', '.join(ALLOWED_REPORTS)}.
Allowed file formats: {', '.join(ALLOWED_FILE_FORMATS)}.
Allowed widget types: {', '.join(ALLOWED_WIDGET_TYPES)}.
Blocked operations: {', '.join(BLOCKED_OPERATIONS)}.
Blocked requests must use intent blocked_write. Export requests use generate_file. Dashboard pin requests use pin_to_dashboard. Do not invent records or results.
Use this exact shape and always include every key:
{json.dumps({'intent':'unsupported','operation':'none','doctype':None,'report_name':None,'record_name':None,'data':{},'filters':{},'fields':[],'file_format':None,'widget_type':None,'date_range':None,'limit':20,'confidence':0.0,'missing_information':[],'blocked_reason':None,'user_facing_summary':None})}"""


def build_rag_system_prompt() -> str:
    return """You answer only from the supplied approved private knowledge context.
Do not use outside knowledge, ERPNext records, transactions, reports, or inferred business data.
If the answer is absent, set insufficient=true and say that you do not know.
Every factual answer must cite one or more supplied citation IDs.
Do not invent procedures. Return JSON only with keys answer, citation_ids, confidence, insufficient."""


def build_assessment_system_prompt() -> str:
    return """Generate assessment questions only from the supplied approved training context.
Return JSON only with a questions array. Each question requires question, four options,
correct_answer matching one option, and a short explanation. Do not introduce facts not
present in the context and do not include ERPNext business records."""
