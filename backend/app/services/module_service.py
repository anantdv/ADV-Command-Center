from app.config import settings
from app.core.exceptions import AppError, PermissionDenied
from app.db.seed import FULL_PERMISSION, MODULE_RECORDS, MODULES
from app.frappe.client import FrappeClient
from app.schemas.common import PermissionMeta
from app.schemas.erpnext import AllowedDoctype
from app.schemas.modules import ModuleDetail, ModuleRecords, ModuleReports, ModuleSummary
from app.services.erpnext_service import ERPNextService
from app.services.report_service import ReportService

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
        doctypes = await ERPNextService(self._client()).get_allowed_doctypes(cookies=cookies)
        summaries = []
        for slug, name, description, _metric, _metric_label, color in MODULES:
            available = self._for_module(doctypes, name)
            if not available:
                continue
            summaries.append(
                ModuleSummary(
                    slug=slug,
                    name=name,
                    description=description,
                    metric=str(len(available)),
                    metric_label="Available DocTypes",
                    color=color,
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

        summaries = await self.list_modules(cookies)
        module = next((item for item in summaries if item.slug == slug), None)
        if not module:
            raise AppError("Module is unavailable or not permitted", 404)
        doctypes = self._for_module(
            await ERPNextService(self._client()).get_allowed_doctypes(cookies=cookies),
            module.name,
        )
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


module_service = ModuleService()
