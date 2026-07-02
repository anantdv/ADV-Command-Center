from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.chat import PermissionMeta, SourceMeta
from app.services.report_service import ReportService


class ReportReadTools:
    def __init__(self, service: ReportService | None = None):
        self.service = service or ReportService(
            FrappeClient(
                settings.frappe_base_url,
                settings.frappe_auth_mode,
                settings.frappe_api_key,
                settings.frappe_api_secret,
                settings.frappe_session_cookie_name,
            )
        )

    async def run_report(
        self,
        report_name: str,
        filters: dict | None = None,
        cookies: dict | None = None,
    ) -> dict[str, Any]:
        result = await self.service.run_report(report_name, filters or {}, cookies)
        rows = result.get("rows") or []
        columns = result.get("columns") or (list(rows[0].keys()) if rows else [])
        return {
            "columns": columns,
            "rows": rows,
            "record_count": len(rows),
            "source": SourceMeta(
                source_type="report",
                source_name=report_name,
                record_count=len(rows),
                filters=filters or {},
                report_name=report_name,
            ).model_dump(),
            "permission": PermissionMeta(
                allowed=True,
                risk_level="low",
                confirmation_required=False,
            ).model_dump(),
        }


REPORT_TOOL_NAMES = ["run_report"]
