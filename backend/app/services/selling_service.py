from app.config import settings
from app.db.seed import FULL_PERMISSION
from app.frappe.client import FrappeClient
from app.schemas.modules import ModuleDashboardResponse, ModuleKPI, ModuleRecentDocument, ModuleReportCard
from app.services.erpnext_service import ERPNextService
from app.utils.selling_dashboard_builder import build_selling_kpis, build_selling_quick_actions, build_selling_recent_documents, build_selling_reports


class SellingService:
    def __init__(self, client: FrappeClient | None = None):
        self.client = client or FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name)
        self.erp = ERPNextService(self.client)

    async def get_dashboard(self, cookies: dict | None = None) -> ModuleDashboardResponse:
        if settings.use_mock_data:
            return _mock_selling_dashboard()
        context = await self.erp.get_current_user_context(cookies)
        allowed = await self.erp.get_allowed_doctypes(cookies=cookies)
        doctypes = [item.name for item in allowed if item.name in {"Customer", "Lead", "Opportunity", "Quotation", "Sales Order", "Sales Invoice", "Delivery Note", "Item"}]
        return ModuleDashboardResponse(
            module_name="Selling",
            label="Selling",
            kpis=await build_selling_kpis(self.erp, cookies, context.company_currency),
            reports=await build_selling_reports(self.erp, cookies),
            recent_documents=await build_selling_recent_documents(self.erp, cookies),
            quick_actions=await build_selling_quick_actions(self.erp, cookies),
            permissions={f"can_read_{doctype.lower().replace(' ', '_')}": True for doctype in doctypes},
            doctypes=doctypes,
        )


def _mock_selling_dashboard() -> ModuleDashboardResponse:
    return ModuleDashboardResponse(
        module_name="Selling",
        label="Selling",
        doctypes=["Customer", "Quotation", "Sales Order", "Sales Invoice", "Delivery Note", "Item"],
        kpis=[
            ModuleKPI(id="total_customers", label="Total Customers", value=152, source_doctype="Customer", action_prompt="show customers"),
            ModuleKPI(id="open_quotations", label="Open Quotations", value=18, source_doctype="Quotation", action_prompt="show open quotations"),
            ModuleKPI(id="open_sales_orders", label="Open Sales Orders", value=24, source_doctype="Sales Order", action_prompt="show open sales orders"),
            ModuleKPI(id="total_sales_this_month", label="Sales This Month", value=1250000, value_type="currency", currency="INR", source_doctype="Sales Invoice", action_prompt="show sales invoices this month"),
            ModuleKPI(id="overdue_sales_invoices", label="Overdue Sales Invoices", value=4, source_doctype="Sales Invoice", action_prompt="show overdue sales invoices"),
            ModuleKPI(id="outstanding_receivable", label="Outstanding Receivable", value=645320, value_type="currency", currency="INR", source_doctype="Sales Invoice", action_prompt="show receivables"),
        ],
        reports=[
            ModuleReportCard(id="monthly_sales_trend", title="Monthly Sales Trend", report_type="chart", chart_type="line", source_doctype="Sales Invoice", data=[{"period": "2026-05", "grand_total_sum": 760000}, {"period": "2026-06", "grand_total_sum": 980000}, {"period": "2026-07", "grand_total_sum": 1250000}], action_prompt="show monthly sales trend"),
            ModuleReportCard(id="top_customers_by_sales", title="Top Customers by Sales", report_type="chart", chart_type="bar", source_doctype="Sales Invoice", data=[{"customer": "Aster Retail Pvt Ltd", "grand_total": 420000}, {"customer": "Nimbus Labs India", "grand_total": 310000}], action_prompt="show top customers by sales"),
            ModuleReportCard(id="unpaid_sales_invoices", title="Unpaid Sales Invoices", report_type="table", source_doctype="Sales Invoice", data=[{"name": "ACC-SINV-2026-00122", "customer": "Aster Retail Pvt Ltd", "posting_date": "2026-07-01", "grand_total": 184500, "outstanding_amount": 184500, "status": "Overdue"}], columns=[{"key": "name", "label": "Invoice"}, {"key": "customer", "label": "Customer"}, {"key": "outstanding_amount", "label": "Outstanding"}], action_prompt="show unpaid sales invoices"),
        ],
        recent_documents=[
            ModuleRecentDocument(doctype="Sales Invoice", name="ACC-SINV-2026-00122", title="ACC-SINV-2026-00122", status="Overdue", party="Aster Retail Pvt Ltd", amount=184500, currency="INR", date="2026-07-01"),
            ModuleRecentDocument(doctype="Sales Order", name="SAL-ORD-2026-0001", title="SAL-ORD-2026-0001", status="To Deliver and Bill", party="Aster Retail Pvt Ltd", amount=225000, currency="INR", date="2026-07-01"),
        ],
        quick_actions=[
            {"id": "create_customer_draft", "label": "Create Customer Draft", "prompt": "create customer draft", "enabled": True},
            {"id": "create_quotation_draft", "label": "Create Quotation Draft", "prompt": "create quotation draft", "enabled": True},
            {"id": "show_pending_selling_approvals", "label": "Show Pending Selling Approvals", "prompt": "show pending selling approvals", "enabled": True},
        ],
        permissions=FULL_PERMISSION,
    )
