from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

from app.schemas.modules import ModuleKPI, ModuleRecentDocument, ModuleReportCard
from app.services.erpnext_service import ERPNextService
from app.utils.filter_normalizer import FilterNormalizationError


SELLING_DOCTYPES = ["Customer", "Lead", "Opportunity", "Quotation", "Sales Order", "Sales Invoice", "Delivery Note", "Item"]


async def build_selling_kpis(erp: ERPNextService, cookies: dict | None = None, currency: str = "INR") -> list[ModuleKPI]:
    kpis: list[ModuleKPI] = []
    customers = await _safe_rows(erp, "Customer", ["name"], {}, cookies)
    _append_count(kpis, "total_customers", "Total Customers", "Customer", customers, "show customers")

    quotations = await _safe_rows(erp, "Quotation", ["name", "status", "grand_total"], {"status": ["not in", ["Lost", "Ordered", "Cancelled"]]}, cookies)
    _append_count(kpis, "open_quotations", "Open Quotations", "Quotation", quotations, "show open quotations")

    orders = await _safe_rows(erp, "Sales Order", ["name", "status", "grand_total"], {"status": ["in", ["To Deliver and Bill", "To Bill", "To Deliver"]]}, cookies)
    _append_count(kpis, "open_sales_orders", "Open Sales Orders", "Sales Order", orders, "show open sales orders")

    month_range = _current_month_range()
    invoices_month = await _safe_rows(erp, "Sales Invoice", ["name", "posting_date", "grand_total", "outstanding_amount", "status"], {}, cookies, month_range)
    _append_count(kpis, "sales_invoices_this_month", "Sales Invoices This Month", "Sales Invoice", invoices_month, "show sales invoices this month")
    if invoices_month is not None:
        kpis.append(ModuleKPI(id="total_sales_this_month", label="Sales This Month", value=_sum(invoices_month, "grand_total"), value_type="currency", currency=currency, source_doctype="Sales Invoice", filters=month_range, action_prompt="show sales invoices this month"))

    unpaid = await _safe_rows(erp, "Sales Invoice", ["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"], {"status": ["in", ["Unpaid", "Overdue"]]}, cookies)
    _append_count(kpis, "unpaid_sales_invoices", "Unpaid Sales Invoices", "Sales Invoice", unpaid, "show unpaid sales invoices")
    if unpaid is not None:
        kpis.append(ModuleKPI(id="outstanding_receivable", label="Outstanding Receivable", value=_sum(unpaid, "outstanding_amount"), value_type="currency", currency=currency, source_doctype="Sales Invoice", filters={"status": ["in", ["Unpaid", "Overdue"]]}, action_prompt="show receivables"))

    overdue = await _safe_rows(erp, "Sales Invoice", ["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"], {"status": "Overdue"}, cookies)
    _append_count(kpis, "overdue_sales_invoices", "Overdue Sales Invoices", "Sales Invoice", overdue, "show overdue sales invoices")
    return kpis


async def build_selling_reports(erp: ERPNextService, cookies: dict | None = None) -> list[ModuleReportCard]:
    reports: list[ModuleReportCard] = []
    invoices = await _safe_rows(erp, "Sales Invoice", ["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"], {}, cookies, {"from_date": f"{date.today().year}-01-01", "to_date": date.today().isoformat()}, 500)
    if invoices is not None:
        reports.extend([
            ModuleReportCard(id="monthly_sales_trend", title="Monthly Sales Trend", report_type="chart", chart_type="line", source_doctype="Sales Invoice", data=_group_by_month(invoices, "posting_date", "grand_total"), action_prompt="show monthly sales trend"),
            ModuleReportCard(id="top_customers_by_sales", title="Top Customers by Sales", report_type="chart", chart_type="bar", source_doctype="Sales Invoice", data=_top_sum(invoices, "customer", "grand_total"), action_prompt="show top customers by sales"),
            ModuleReportCard(id="top_customers_by_outstanding", title="Top Customers by Outstanding", report_type="chart", chart_type="bar", source_doctype="Sales Invoice", data=_top_sum([row for row in invoices if _num(row.get("outstanding_amount")) > 0], "customer", "outstanding_amount"), action_prompt="show top customers by outstanding"),
        ])
        unpaid = [row for row in invoices if row.get("status") in {"Unpaid", "Overdue"} or _num(row.get("outstanding_amount")) > 0]
        reports.append(ModuleReportCard(id="unpaid_sales_invoices", title="Unpaid Sales Invoices", report_type="table", source_doctype="Sales Invoice", data=unpaid[:10], columns=_columns(unpaid), action_prompt="show unpaid sales invoices"))

    orders = await _safe_rows(erp, "Sales Order", ["name", "status", "grand_total"], {}, cookies)
    if orders is not None:
        reports.append(ModuleReportCard(id="sales_orders_by_status", title="Sales Orders by Status", report_type="chart", chart_type="pie", source_doctype="Sales Order", data=_counts(orders, "status"), action_prompt="show sales orders by status"))

    quotations = await _safe_rows(erp, "Quotation", ["name", "status", "grand_total"], {}, cookies)
    if quotations is not None:
        reports.append(ModuleReportCard(id="quotations_by_status", title="Quotations by Status", report_type="chart", chart_type="pie", source_doctype="Quotation", data=_counts(quotations, "status"), action_prompt="show quotations by status"))
    return reports


async def build_selling_recent_documents(erp: ERPNextService, cookies: dict | None = None) -> list[ModuleRecentDocument]:
    output: list[ModuleRecentDocument] = []
    specs = [
        ("Customer", ["name", "customer_name", "modified"], {}),
        ("Quotation", ["name", "party_name", "transaction_date", "grand_total", "status", "modified"], {}),
        ("Sales Order", ["name", "customer", "transaction_date", "grand_total", "status", "modified"], {}),
        ("Sales Invoice", ["name", "customer", "posting_date", "grand_total", "status", "modified"], {}),
    ]
    for doctype, fields, filters in specs:
        rows = await _safe_rows(erp, doctype, fields, filters, cookies, limit=5)
        if rows is None:
            continue
        for row in rows[:5]:
            output.append(ModuleRecentDocument(doctype=doctype, name=str(row.get("name")), title=str(row.get("customer_name") or row.get("name")), status=row.get("status"), party=row.get("customer") or row.get("party_name") or row.get("customer_name"), amount=row.get("grand_total"), currency=row.get("currency"), date=row.get("posting_date") or row.get("transaction_date"), modified=str(row.get("modified") or "")))
    return output[:20]


async def build_selling_quick_actions(erp: ERPNextService, cookies: dict | None = None) -> list[dict[str, Any]]:
    actions = [{"id": "show_pending_selling_approvals", "label": "Show Pending Selling Approvals", "prompt": "show pending selling approvals", "enabled": True}]
    for doctype, prompt in [
        ("Customer", "create customer draft"),
        ("Quotation", "create quotation draft"),
        ("Sales Order", "create sales order draft"),
        ("Sales Invoice", "create sales invoice draft"),
    ]:
        try:
            permission = await erp.check_permission("create", doctype, cookies=cookies)
            if permission.allowed or permission.can_create:
                actions.append({"id": f"create_{doctype.lower().replace(' ', '_')}_draft", "label": f"Create {doctype} Draft", "prompt": prompt, "enabled": True, "doctype": doctype})
        except Exception:
            continue
    return actions


async def _safe_rows(erp: ERPNextService, doctype: str, fields: list[str], filters: dict[str, Any] | None, cookies: dict | None, date_range: dict[str, str] | None = None, limit: int = 500) -> list[dict[str, Any]] | None:
    try:
        return (await erp.list_records(doctype, filters or {}, fields, limit, cookies=cookies, date_range=date_range)).records
    except (FilterNormalizationError, Exception):
        return None


def _append_count(kpis: list[ModuleKPI], key: str, label: str, doctype: str, rows: list[dict[str, Any]] | None, prompt: str) -> None:
    if rows is not None:
        kpis.append(ModuleKPI(id=key, label=label, value=len(rows), source_doctype=doctype, action_prompt=prompt))


def _current_month_range() -> dict[str, str]:
    today = date.today()
    return {"from_date": today.replace(day=1).isoformat(), "to_date": today.isoformat()}


def _num(value: Any) -> float:
    try:
        return float(str(value or 0).replace("₹", "").replace(",", ""))
    except ValueError:
        return 0


def _sum(rows: list[dict[str, Any]], field: str) -> float:
    return round(sum(_num(row.get(field)) for row in rows), 2)


def _top_sum(rows: list[dict[str, Any]], group_key: str, value_key: str, limit: int = 10) -> list[dict[str, Any]]:
    grouped: dict[str, float] = defaultdict(float)
    for row in rows:
        grouped[str(row.get(group_key) or "Unknown")] += _num(row.get(value_key))
    return [{group_key: key, value_key: round(value, 2)} for key, value in sorted(grouped.items(), key=lambda item: item[1], reverse=True)[:limit]]


def _counts(rows: list[dict[str, Any]], key: str) -> list[dict[str, Any]]:
    counts = Counter(str(row.get(key) or "Unknown") for row in rows)
    return [{key: label, "count": count} for label, count in counts.most_common()]


def _group_by_month(rows: list[dict[str, Any]], date_key: str, value_key: str) -> list[dict[str, Any]]:
    grouped: dict[str, float] = defaultdict(float)
    for row in rows:
        period = str(row.get(date_key) or "")[:7] or "Unknown"
        grouped[period] += _num(row.get(value_key))
    return [{"period": key, f"{value_key}_sum": round(value, 2)} for key, value in sorted(grouped.items())]


def _columns(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    return [{"key": key, "label": key.replace("_", " ").title()} for key in rows[0] if not key.startswith("_")]
