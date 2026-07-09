from app.config import settings
from app.core.exceptions import AppError, PermissionDenied
from app.db.seed import FULL_PERMISSION, MODULE_RECORDS, MODULES
from app.frappe.client import FrappeClient
from app.schemas.common import PermissionMeta
from app.schemas.erpnext import AllowedDoctype
from app.schemas.modules import ModuleDashboardResponse, ModuleDetail, ModuleDoctypeInfo, ModuleDoctypeNavigationResponse, ModuleDoctypeRecordsResponse, ModuleKPI, ModuleRecords, ModuleReports, ModuleSummary
from app.services.erpnext_service import ERPNextService
from app.services.report_service import ReportService
from app.services.selling_service import SellingService
from app.utils.module_doctype_registry import find_module_doctype, module_doctypes
from app.utils.module_permission_builder import ModulePermissionBuilder
from app.utils.module_registry import MODULE_REGISTRY, normalize_module_name

ERP_MODULE_MAP = {
    "Accounting": ["Accounts"],
    "Selling": ["Selling"],
    "Buying": ["Buying"],
    "Stock": ["Stock"],
    "CRM": ["CRM"],
    "Projects": ["Projects"],
    "HR": ["HR", "HRMS"],
    "Manufacturing": ["Manufacturing"],
}

PRIMARY_DOCTYPES = {
    "Accounting": "GL Entry",
    "Selling": "Sales Invoice",
    "Buying": "Purchase Order",
    "Stock": "Item",
    "CRM": "Lead",
    "Projects": "Project",
    "HR": "Employee",
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
                slug=slug,
                name=name,
                description=description,
                metric=metric,
                metric_label=metric_label,
                color=color,
                permissions=permission,
            )
            for slug, name, description, metric, metric_label, color in MODULES
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
            return ModuleDashboardResponse(module_name=summary.name, label=summary.name, doctypes=[], kpis=[ModuleKPI(id="available_doctypes", label="Available DocTypes", value=summary.metric)], reports=[], recent_documents=[], quick_actions=[{"id": "ask_module_ai", "label": f"Ask {summary.name} AI", "prompt": f"show {summary.name.lower()} records", "enabled": True}], permissions=summary.permissions.model_dump(), pinned_widgets=await self._pinned_widgets(summary.name, cookies, user, roles))
        modules = await ModulePermissionBuilder(ERPNextService(self._client())).get_accessible_modules(cookies)
        module = next((item for item in modules if item.module_name.lower() == normalized.lower()), None)
        if not module:
            raise AppError(f"You do not have permission to access the {normalized} module.", 403)
        return ModuleDashboardResponse(
            module_name=module.module_name,
            label=module.label,
            doctypes=module.doctypes,
            kpis=[ModuleKPI(id="available_doctypes", label="Available DocTypes", value=len(module.doctypes), value_type="number")],
            reports=[],
            recent_documents=[],
            quick_actions=[{"id": "ask_module_ai", "label": f"Ask {module.label} AI", "prompt": f"show {module.label.lower()} records", "enabled": True}],
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

    @staticmethod
    def _for_module(doctypes: list[AllowedDoctype], frontend_name: str) -> list[AllowedDoctype]:
        modules = set(ERP_MODULE_MAP.get(frontend_name, []))
        return [item for item in doctypes if item.module in modules]

    @staticmethod
    def _frontend_name(slug_or_name: str) -> str:
        normalized = slug_or_name.lower()
        for slug, name, *_ in MODULES:
            if normalized in {slug, name.lower()}:
                return name
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

    @staticmethod
    async def _pinned_widgets(module_name: str, cookies: dict | None, user: str, roles: list[str] | None) -> list[dict]:
        from app.services.dashboard_service import dashboard_service

        widgets = await dashboard_service.list_module_widgets(module_name, cookies, user, roles)
        return [widget.model_dump(mode="json") for widget in widgets]


module_service = ModuleService()


def _module_color(module_name: str) -> str:
    return {"Selling": "indigo", "Buying": "emerald", "Stock": "amber", "Accounts": "blue", "CRM": "violet", "Projects": "cyan", "HR": "rose", "Manufacturing": "orange"}.get(module_name, "indigo")
