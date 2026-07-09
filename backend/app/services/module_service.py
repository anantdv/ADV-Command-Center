from app.config import settings
from app.core.exceptions import AppError, PermissionDenied
from app.db.seed import FULL_PERMISSION, MODULE_RECORDS, MODULES
from app.frappe.client import FrappeClient
from app.schemas.common import PermissionMeta
from app.schemas.dashboard import DashboardWidgetData
from app.schemas.erpnext import AllowedDoctype, DocumentDetailResponse
from app.schemas.modules import ModuleDashboardResponse, ModuleDetail, ModuleDoctypeInfo, ModuleDoctypeNavigationResponse, ModuleDoctypeRecordsResponse, ModuleKPI, ModuleRecentDocument, ModuleRecords, ModuleReportCard, ModuleReports, ModuleSummary
from app.services.erpnext_service import ERPNextService
from app.services.report_service import ReportService
from app.services.selling_service import SellingService
from app.utils.module_doctype_registry import find_module_doctype, module_doctypes
from app.utils.module_permission_builder import ModulePermissionBuilder
from app.utils.module_registry import MODULE_REGISTRY, normalize_module_name

ERP_MODULE_MAP = {
    "Accounting": ["Accounts"],
    "Accounts": ["Accounts"],
    "Selling": ["Selling"],
    "Buying": ["Buying"],
    "Stock": ["Stock"],
    "CRM": ["CRM"],
    "Projects": ["Projects"],
    "Support": ["Support"],
    "HR": ["HR", "HRMS"],
    "Assets": ["Assets"],
    "Manufacturing": ["Manufacturing"],
}

PRIMARY_DOCTYPES = {
    "Accounting": "GL Entry",
    "Selling": "Sales Invoice",
    "Buying": "Purchase Order",
    "Stock": "Item",
    "CRM": "Lead",
    "Projects": "Project",
    "Support": "Issue",
    "HR": "Employee",
    "Assets": "Asset",
    "Manufacturing": "Work Order",
}


class ModuleService:
    def __init__(self, client: FrappeClient | None = None):
        self.client = client

    def _client(self) -> FrappeClient:
        return self.client or FrappeClient(
            settings.frappe_base_url,
            settings.frappe_auth_mode,
            settings.frappe_api_key,
            settings.frappe_api_secret,
            settings.frappe_session_cookie_name,
        )

    def _mock_summaries(self) -> list[ModuleSummary]:
        permission = PermissionMeta(**FULL_PERMISSION)
        return [
            ModuleSummary(
                slug=config["route"].split("/")[-1],
                name=config["label"],
                description=config.get("description") or "",
                metric=str(len(config.get("doctypes") or [])),
                metric_label="Configured DocTypes",
                color=_module_color(module_name),
                permissions=permission,
            )
            for module_name, config in MODULE_REGISTRY.items()
        ]

    async def list_modules(self, cookies: dict | None = None) -> list[ModuleSummary]:
        if settings.use_mock_data:
            return self._mock_summaries()
        erp = ERPNextService(self._client())
        accessible = await ModulePermissionBuilder(erp).get_accessible_modules(cookies)
        summaries = []
        for module in accessible:
            slug = module.module_name.lower()
            summaries.append(
                ModuleSummary(
                    slug=slug,
                    name=module.label,
                    description=module.description or "",
                    metric=str(len(module.doctypes)),
                    metric_label="Available DocTypes",
                    color=_module_color(module.module_name),
                    permissions=PermissionMeta(allowed=True, can_read=True),
                )
            )
        return summaries

    async def get_module(self, name: str, cookies: dict | None = None) -> ModuleDetail:
        slug = name.lower()
        if settings.use_mock_data:
            module = next((item for item in self._mock_summaries() if item.slug == slug), None)
            if not module:
                raise AppError("Module not found", 404)
            records = MODULE_RECORDS.get(slug, [])
            return ModuleDetail(module=module, records=records, reports=records[:3])

        module_name = normalize_module_name(name)
        summaries = await self.list_modules(cookies)
        module = next((item for item in summaries if item.slug == slug or item.name == module_name), None)
        if not module:
            raise AppError("Module is unavailable or not permitted", 404)
        allowed_names = set((await self.get_module_dashboard(module.name, cookies)).doctypes)
        doctypes = [AllowedDoctype(name=item, label=item, module=module.name, permissions=PermissionMeta(allowed=True, can_read=True)) for item in allowed_names]
        reports = await self._report_names(module.name, cookies)
        return ModuleDetail(
            module=module,
            records=[item.name for item in doctypes],
            reports=reports,
        )

    async def records(self, name: str, cookies: dict | None = None) -> ModuleRecords:
        if settings.use_mock_data:
            records = [
                {"name": f"{name.upper()}-{1000 + index}", "title": title}
                for index, title in enumerate(MODULE_RECORDS.get(name.lower(), []))
            ]
            return ModuleRecords(
                records=records,
                permissions=PermissionMeta(**FULL_PERMISSION),
            )

        module_name = self._frontend_name(name)
        allowed = self._for_module(
            await ERPNextService(self._client()).get_allowed_doctypes(cookies=cookies),
            module_name,
        )
        if not allowed:
            return ModuleRecords(records=[], permissions=PermissionMeta(allowed=False, can_read=False, reason="No permitted DocTypes"))
        allowed_names = {item.name for item in allowed}
        doctype = PRIMARY_DOCTYPES.get(module_name)
        if doctype not in allowed_names:
            doctype = allowed[0].name
        try:
            result = await ERPNextService(self._client()).list_records(
                doctype=doctype,
                fields=["name"],
                limit=20,
                cookies=cookies,
            )
            return ModuleRecords(records=result.records, permissions=result.permissions)
        except PermissionDenied:
            return ModuleRecords(records=[], permissions=PermissionMeta(allowed=True, can_read=True))

    async def reports(self, name: str, cookies: dict | None = None) -> ModuleReports:
        if settings.use_mock_data:
            return ModuleReports(
                reports=MODULE_RECORDS.get(name.lower(), [])[:3],
                permissions=PermissionMeta(**FULL_PERMISSION),
            )
        module_name = self._frontend_name(name)
        reports = await self._report_names(module_name, cookies)
        return ModuleReports(
            reports=reports,
            permissions=PermissionMeta(allowed=True, can_read=True),
        )

    async def get_module_dashboard(self, module_name: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> ModuleDashboardResponse:
        normalized = normalize_module_name(module_name)
        if normalized == "Selling":
            dashboard = await SellingService(self._client()).get_dashboard(cookies)
            dashboard.pinned_widgets = await self._pinned_widgets(normalized, cookies, user, roles)
            return dashboard
        if settings.use_mock_data:
            summaries = self._mock_summaries()
            summary = next((item for item in summaries if item.name.lower() == normalized.lower() or item.slug == module_name.lower()), None)
            if not summary:
                raise AppError("Module not found", 404)
            doctypes = [item["doctype"] for item in module_doctypes(summary.name)]
            return ModuleDashboardResponse(module_name=summary.name, label=summary.name, doctypes=doctypes, kpis=self._dashboard_kpis(summary.name, doctypes, {}), reports=self._dashboard_report_cards(summary.name), recent_documents=self._mock_recent_documents(summary.name, doctypes), quick_actions=self._quick_actions(summary.name), permissions=summary.permissions.model_dump(), pinned_widgets=await self._pinned_widgets(summary.name, cookies, user, roles))
        modules = await ModulePermissionBuilder(ERPNextService(self._client())).get_accessible_modules(cookies)
        module = next((item for item in modules if item.module_name.lower() == normalized.lower()), None)
        if not module:
            raise AppError(f"You do not have permission to access the {normalized} module.", 403)
        return ModuleDashboardResponse(
            module_name=module.module_name,
            label=module.label,
            doctypes=module.doctypes,
            kpis=await self._live_kpis(module.module_name, module.doctypes, cookies),
            reports=self._dashboard_report_cards(module.module_name),
            recent_documents=await self._live_recent_documents(module.module_name, module.doctypes, cookies),
            quick_actions=self._quick_actions(module.module_name),
            permissions={"accessible": True},
            pinned_widgets=await self._pinned_widgets(module.module_name, cookies, user, roles),
        )

    async def get_module_doctypes(self, module_name: str, cookies: dict | None = None) -> ModuleDoctypeNavigationResponse:
        normalized = normalize_module_name(module_name)
        registered = module_doctypes(normalized)
        if not registered:
            dashboard = await self.get_module_dashboard(normalized, cookies)
            registered = [{"doctype": doctype, "label": doctype, "description": f"{doctype} records", "icon": "file-text", "default_fields": ["name"]} for doctype in dashboard.doctypes]
        allowed = {item["doctype"] for item in registered} if settings.use_mock_data else {item.name for item in await ERPNextService(self._client()).get_allowed_doctypes(cookies=cookies)}
        erp = ERPNextService(self._client())
        output: list[ModuleDoctypeInfo] = []
        for item in registered:
            doctype = item["doctype"]
            if doctype not in allowed:
                continue
            can_create = False
            try:
                permission = await erp.check_permission("create", doctype, cookies=cookies)
                can_create = permission.allowed or permission.can_create
            except Exception:
                pass
            count = None
            try:
                count = len((await erp.list_records(doctype, {}, ["name"], 500, cookies=cookies)).records)
            except Exception:
                pass
            output.append(ModuleDoctypeInfo(doctype=doctype, label=item.get("label") or doctype, description=item.get("description"), icon=item.get("icon"), can_read=True, can_create=can_create, record_count=count, route=f"/modules/{normalized.lower()}/doctype/{doctype}", default_fields=item.get("default_fields") or ["name"]))
        return ModuleDoctypeNavigationResponse(module_name=normalized, doctypes=output)

    async def get_module_doctype_records(self, module_name: str, doctype: str, page: int = 1, page_size: int = 20, search: str | None = None, order_by: str | None = None, fields: list[str] | None = None, cookies: dict | None = None) -> ModuleDoctypeRecordsResponse:
        normalized = normalize_module_name(module_name)
        config = find_module_doctype(normalized, doctype)
        if not config:
            raise AppError("This document type is not part of the selected module.", 404, {"module_name": normalized, "doctype": doctype})
        requested_fields = fields or config.get("default_fields") or ["name"]
        erp = ERPNextService(self._client())
        records = (await erp.list_records(doctype, {}, requested_fields, 500, order_by or config.get("default_order_by"), cookies=cookies)).records
        if search:
            search_lower = search.lower()
            search_fields = config.get("search_fields") or ["name"]
            records = [row for row in records if any(search_lower in str(row.get(field, "")).lower() for field in search_fields)]
        total = len(records)
        page = max(1, page)
        page_size = max(1, min(page_size, 100))
        start = (page - 1) * page_size
        rows = [dict(row) | {"_meta": {"doctype": doctype, "name": str(row.get("name")), "clickable": True}} for row in records[start:start + page_size]]
        columns = [{"key": field, "label": field.replace("_", " ").title()} for field in requested_fields]
        return ModuleDoctypeRecordsResponse(module_name=normalized, doctype=doctype, page=page, page_size=page_size, total=total, columns=columns, rows=rows)

    async def get_module_doctype_record_detail(self, module_name: str, doctype: str, name: str, cookies: dict | None = None) -> DocumentDetailResponse:
        normalized = normalize_module_name(module_name)
        if not find_module_doctype(normalized, doctype):
            raise AppError("This document type is not part of the selected module.", 404, {"module_name": normalized, "doctype": doctype})
        return await ERPNextService(self._client()).get_document_detail(doctype, name, cookies)

    async def get_pinned_widgets(self, module_name: str, cookies: dict | None = None, user: str = "unknown", roles: list[str] | None = None) -> list[DashboardWidgetData]:
        normalized = normalize_module_name(module_name)
        if normalized not in MODULE_REGISTRY:
            raise AppError("This module is not available or you do not have permission to access it.", 404)
        from app.services.dashboard_service import dashboard_service

        return await dashboard_service.list_module_widgets(normalized, cookies, user, roles)

    @staticmethod
    def _for_module(doctypes: list[AllowedDoctype], frontend_name: str) -> list[AllowedDoctype]:
        modules = set(ERP_MODULE_MAP.get(frontend_name, []))
        return [item for item in doctypes if item.module in modules]

    @staticmethod
    def _frontend_name(slug_or_name: str) -> str:
        module_name = normalize_module_name(slug_or_name)
        if module_name in MODULE_REGISTRY:
            return module_name
        raise AppError("Module not found", 404)

    async def _report_names(self, frontend_name: str, cookies: dict | None) -> list[str]:
        service = ReportService(self._client())
        reports: list[str] = []
        for frappe_module in ERP_MODULE_MAP.get(frontend_name, []):
            for report in await service.get_allowed_reports(frappe_module, cookies):
                name = report.get("name") or report.get("report_name")
                if name and name not in reports:
                    reports.append(name)
        return reports[:20]

    def _dashboard_kpis(self, module_name: str, doctypes: list[str], counts: dict[str, int]) -> list[ModuleKPI]:
        specs = MODULE_KPI_SPECS.get(normalize_module_name(module_name), [])
        kpis = [ModuleKPI(id="available_doctypes", label="Available DocTypes", value=len(doctypes), value_type="number", action_prompt=f"show {module_name.lower()} records")]
        for spec in specs:
            doctype = spec.get("doctype")
            if doctype and doctype not in doctypes:
                continue
            kpis.append(ModuleKPI(id=spec["id"], label=spec["label"], value=counts.get(doctype or "", 0), value_type=spec.get("value_type", "number"), source_doctype=doctype, action_prompt=spec.get("prompt")))
        return kpis[:8]

    async def _live_kpis(self, module_name: str, doctypes: list[str], cookies: dict | None) -> list[ModuleKPI]:
        counts: dict[str, int] = {}
        erp = ERPNextService(self._client())
        for doctype in doctypes[:10]:
            try:
                counts[doctype] = len((await erp.list_records(doctype, {}, ["name"], 500, cookies=cookies)).records)
            except Exception:
                continue
        return self._dashboard_kpis(module_name, doctypes, counts)

    def _dashboard_report_cards(self, module_name: str) -> list[ModuleReportCard]:
        normalized = normalize_module_name(module_name)
        cards: list[ModuleReportCard] = []
        for index, report in enumerate((MODULE_REGISTRY.get(normalized) or {}).get("reports", [])[:6]):
            cards.append(ModuleReportCard(id=f"report_{index}", title=report, description=f"Open {report} in Command Center.", report_type="standard_report", report_name=report, data=[], columns=[], action_prompt=f"show {report.lower()}"))
        for title, prompt in MODULE_REPORT_SHORTCUTS.get(normalized, [])[:3]:
            cards.append(ModuleReportCard(id=title.lower().replace(" ", "_"), title=title, description=f"Analyze {title.lower()} with Tinni.", report_type="analytics", data=[], columns=[], action_prompt=prompt))
        return cards[:8]

    async def _live_recent_documents(self, module_name: str, doctypes: list[str], cookies: dict | None) -> list[ModuleRecentDocument]:
        erp = ERPNextService(self._client())
        docs: list[ModuleRecentDocument] = []
        for doctype in doctypes[:4]:
            config = find_module_doctype(module_name, doctype) or {"default_fields": ["name", "status", "modified"]}
            fields = list(dict.fromkeys(["name", "status", "modified", *(config.get("default_fields") or [])]))[:8]
            try:
                rows = (await erp.list_records(doctype, {}, fields, 2, config.get("default_order_by") or "modified desc", cookies=cookies)).records
            except Exception:
                continue
            for row in rows:
                docs.append(self._document_from_row(doctype, row))
        return docs[:8]

    @staticmethod
    def _mock_recent_documents(module_name: str, doctypes: list[str]) -> list[ModuleRecentDocument]:
        return [ModuleRecentDocument(doctype=doctype, name=f"{doctype.upper().replace(' ', '-')}-0001", title=f"{doctype} sample", status="Open") for doctype in doctypes[:4]]

    @staticmethod
    def _document_from_row(doctype: str, row: dict) -> ModuleRecentDocument:
        party = row.get("customer") or row.get("supplier") or row.get("party") or row.get("employee_name") or row.get("project_name") or row.get("subject")
        amount = row.get("grand_total") or row.get("outstanding_amount") or row.get("paid_amount") or row.get("opportunity_amount")
        date = row.get("posting_date") or row.get("transaction_date") or row.get("modified") or row.get("creation")
        return ModuleRecentDocument(doctype=doctype, name=str(row.get("name")), title=str(row.get("name")), status=row.get("status"), party=party, amount=amount if isinstance(amount, (int, float)) else None, currency=row.get("currency"), date=str(date) if date else None, modified=str(row.get("modified")) if row.get("modified") else None)

    @staticmethod
    def _quick_actions(module_name: str) -> list[dict]:
        normalized = normalize_module_name(module_name)
        configured = MODULE_QUICK_ACTIONS.get(normalized, [])
        if configured:
            return configured
        return [{"id": "ask_ai", "label": f"Ask AI about {normalized}", "prompt": f"show {normalized.lower()} records", "enabled": True}, {"id": "generate_report", "label": f"Generate {normalized} Report", "prompt": f"generate {normalized.lower()} report", "enabled": True}]

    @staticmethod
    async def _pinned_widgets(module_name: str, cookies: dict | None, user: str, roles: list[str] | None) -> list[dict]:
        from app.services.dashboard_service import dashboard_service

        widgets = await dashboard_service.list_module_widgets(module_name, cookies, user, roles)
        return [widget.model_dump(mode="json") for widget in widgets]


module_service = ModuleService()


def _module_color(module_name: str) -> str:
    return {"Selling": "blue", "Buying": "amber", "Stock": "emerald", "Accounts": "indigo", "CRM": "violet", "Projects": "cyan", "Support": "sky", "HR": "rose", "Assets": "slate", "Manufacturing": "orange"}.get(normalize_module_name(module_name), "indigo")


MODULE_KPI_SPECS = {
    "Buying": [{"id": "total_suppliers", "label": "Total Suppliers", "doctype": "Supplier", "prompt": "show suppliers"}, {"id": "open_purchase_orders", "label": "Purchase Orders", "doctype": "Purchase Order", "prompt": "show purchase orders"}, {"id": "purchase_invoices", "label": "Purchase Invoices", "doctype": "Purchase Invoice", "prompt": "show purchase invoices"}, {"id": "material_requests", "label": "Material Requests", "doctype": "Material Request", "prompt": "show material requests"}],
    "Stock": [{"id": "total_items", "label": "Total Items", "doctype": "Item", "prompt": "show items"}, {"id": "warehouses", "label": "Warehouses", "doctype": "Warehouse", "prompt": "show warehouses"}, {"id": "stock_entries", "label": "Stock Entries", "doctype": "Stock Entry", "prompt": "show stock entries"}, {"id": "material_requests", "label": "Open Material Requests", "doctype": "Material Request", "prompt": "show material requests"}],
    "Accounts": [{"id": "sales_invoices", "label": "Sales Invoices", "doctype": "Sales Invoice", "prompt": "show sales invoices"}, {"id": "purchase_invoices", "label": "Purchase Invoices", "doctype": "Purchase Invoice", "prompt": "show purchase invoices"}, {"id": "payment_entries", "label": "Payments", "doctype": "Payment Entry", "prompt": "show payments"}, {"id": "journal_entries", "label": "Journal Entries", "doctype": "Journal Entry", "prompt": "show journal entries"}],
    "CRM": [{"id": "open_leads", "label": "Leads", "doctype": "Lead", "prompt": "show leads"}, {"id": "opportunities", "label": "Opportunities", "doctype": "Opportunity", "prompt": "show opportunities"}, {"id": "customers", "label": "Customers", "doctype": "Customer", "prompt": "show customers"}],
    "Projects": [{"id": "projects", "label": "Projects", "doctype": "Project", "prompt": "show projects"}, {"id": "tasks", "label": "Tasks", "doctype": "Task", "prompt": "show tasks"}, {"id": "timesheets", "label": "Timesheets", "doctype": "Timesheet", "prompt": "show timesheets"}],
    "Support": [{"id": "issues", "label": "Open Issues", "doctype": "Issue", "prompt": "show open issues"}, {"id": "customers", "label": "Customers", "doctype": "Customer", "prompt": "show customers"}],
    "HR": [{"id": "employees", "label": "Employees", "doctype": "Employee", "prompt": "show employees"}, {"id": "attendance", "label": "Attendance", "doctype": "Attendance", "prompt": "show attendance"}, {"id": "leave_applications", "label": "Leave Applications", "doctype": "Leave Application", "prompt": "show leave applications"}],
    "Assets": [{"id": "assets", "label": "Total Assets", "doctype": "Asset", "prompt": "show assets"}, {"id": "asset_repairs", "label": "Asset Repairs", "doctype": "Asset Repair", "prompt": "show asset repairs"}],
    "Manufacturing": [{"id": "work_orders", "label": "Work Orders", "doctype": "Work Order", "prompt": "show work orders"}, {"id": "boms", "label": "BOM Count", "doctype": "BOM", "prompt": "show BOMs"}, {"id": "job_cards", "label": "Job Cards", "doctype": "Job Card", "prompt": "show job cards"}],
}


MODULE_REPORT_SHORTCUTS = {
    "Buying": [("Unpaid Purchase Invoices", "show unpaid purchase invoices"), ("Purchase Orders by Supplier", "show purchase orders by supplier")],
    "Stock": [("Stock Entries by Type", "show stock entries by type"), ("Items by Item Group", "show items by item group")],
    "Accounts": [("Receivables Aging", "show receivables"), ("Payables Aging", "show payables"), ("Payment Trend", "show payments")],
    "CRM": [("Opportunity Pipeline", "show opportunity pipeline"), ("Lead Status Summary", "show leads by status")],
    "Projects": [("Tasks by Status", "show tasks by status"), ("Overdue Tasks", "show overdue tasks")],
    "Support": [("Issues by Status", "show issues by status"), ("High Priority Issues", "show high priority issues")],
    "HR": [("Employees by Department", "show employees by department"), ("Leave Applications by Status", "show leave applications by status")],
    "Assets": [("Assets by Category", "show assets by category"), ("Assets Under Maintenance", "show assets under maintenance")],
    "Manufacturing": [("Work Orders by Status", "show work orders by status"), ("Job Cards by Status", "show job cards by status")],
}


MODULE_QUICK_ACTIONS = {
    "Buying": [{"id": "create_supplier", "label": "Create Supplier Draft", "prompt": "create supplier draft", "enabled": True}, {"id": "create_po", "label": "Create Purchase Order Draft", "prompt": "create purchase order draft", "enabled": True}, {"id": "show_pending", "label": "Show Pending Buying Approvals", "prompt": "show pending buying approvals", "enabled": True}, {"id": "report", "label": "Generate Buying Report", "prompt": "generate buying report", "enabled": True}],
    "Stock": [{"id": "create_mr", "label": "Create Material Request Draft", "prompt": "create material request draft", "enabled": True}, {"id": "stock_balance", "label": "Show Stock Balance", "prompt": "show stock balance", "enabled": True}, {"id": "low_stock", "label": "Show Low Stock Items", "prompt": "show low stock items", "enabled": True}],
    "Accounts": [{"id": "receivables", "label": "Show Receivables", "prompt": "show receivables", "enabled": True}, {"id": "payables", "label": "Show Payables", "prompt": "show payables", "enabled": True}, {"id": "ledger", "label": "Show General Ledger", "prompt": "show general ledger", "enabled": True}, {"id": "report", "label": "Generate Accounts Report", "prompt": "generate accounts report", "enabled": True}],
    "CRM": [{"id": "create_lead", "label": "Create Lead Draft", "prompt": "create lead draft", "enabled": True}, {"id": "create_opportunity", "label": "Create Opportunity Draft", "prompt": "create opportunity draft", "enabled": True}, {"id": "open_opportunities", "label": "Show Open Opportunities", "prompt": "show open opportunities", "enabled": True}],
    "Projects": [{"id": "create_project", "label": "Create Project Draft", "prompt": "create project draft", "enabled": True}, {"id": "create_task", "label": "Create Task Draft", "prompt": "create task draft", "enabled": True}, {"id": "overdue_tasks", "label": "Show Overdue Tasks", "prompt": "show overdue tasks", "enabled": True}],
    "Support": [{"id": "create_issue", "label": "Create Issue Draft", "prompt": "create issue draft", "enabled": True}, {"id": "open_issues", "label": "Show Open Issues", "prompt": "show open issues", "enabled": True}, {"id": "high_priority", "label": "Show High Priority Issues", "prompt": "show high priority issues", "enabled": True}],
    "HR": [{"id": "leave", "label": "Show Pending Leave Applications", "prompt": "show pending leave applications", "enabled": True}, {"id": "attendance", "label": "Show Attendance Today", "prompt": "show attendance today", "enabled": True}, {"id": "claims", "label": "Show Expense Claims", "prompt": "show expense claims", "enabled": True}],
    "Assets": [{"id": "create_asset", "label": "Create Asset Draft", "prompt": "create asset draft", "enabled": True}, {"id": "maintenance", "label": "Show Assets Under Maintenance", "prompt": "show assets under maintenance", "enabled": True}],
    "Manufacturing": [{"id": "create_work_order", "label": "Create Work Order Draft", "prompt": "create work order draft", "enabled": True}, {"id": "open_work_orders", "label": "Show Open Work Orders", "prompt": "show open work orders", "enabled": True}, {"id": "job_cards", "label": "Show Job Cards", "prompt": "show job cards", "enabled": True}],
}
