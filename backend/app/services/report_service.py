from typing import Any

from app.config import settings
from app.frappe import reports as frappe_reports
from app.frappe.client import FrappeClient


class ReportService:
    """Permission-aware facade for existing Frappe Script and Query Reports."""

    def __init__(self, client: FrappeClient):
        self.client = client

    async def get_allowed_reports(
        self,
        module: str | None = None,
        cookies: dict | None = None,
    ) -> list[dict[str, Any]]:
        if settings.use_mock_data:
            return []
        payload = await frappe_reports.get_allowed_reports(self.client, module, cookies)
        return self._unwrap(payload) or []

    async def run_report(
        self,
        report_name: str,
        filters: dict | None = None,
        cookies: dict | None = None,
    ) -> dict[str, Any]:
        if settings.use_mock_data:
            return {
                "columns": ["party", "posting_date", "outstanding_amount"],
                "rows": [
                    {"party": "Aster Retail Pvt Ltd", "posting_date": "2026-07-01", "outstanding_amount": 184500},
                    {"party": "Nimbus Labs India", "posting_date": "2026-07-02", "outstanding_amount": 142800},
                ],
                "truncated": False,
            }
        payload = await frappe_reports.run_report(
            self.client,
            report_name,
            filters or {},
            cookies,
        )
        return self._unwrap(payload) or {}

    @staticmethod
    def _unwrap(payload: dict[str, Any]) -> Any:
        companion = payload.get("message", payload)
        if isinstance(companion, dict) and "success" in companion:
            return companion.get("data")
        return companion
