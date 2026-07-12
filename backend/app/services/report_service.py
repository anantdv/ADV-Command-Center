from typing import Any
from datetime import date

from app.config import settings
from app.frappe import reports as frappe_reports
from app.frappe.client import FrappeClient
from app.services.erpnext_service import ERPNextService


class ReportService:
    """Facade for existing Frappe Script and Query Reports."""

    def __init__(self, client: FrappeClient):
        self.client = client
        self.erp = ERPNextService(client)

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
        filters = await default_report_filters(report_name, filters or {}, self.erp, cookies)
        if settings.use_mock_data:
            return {
                "columns": [{"fieldname": "party", "label": "Party"}, {"fieldname": "posting_date", "label": "Posting Date"}, {"fieldname": "outstanding_amount", "label": "Outstanding Amount"}],
                "rows": [
                    {"party": "Aster Retail Pvt Ltd", "posting_date": "2026-07-01", "outstanding_amount": 184500},
                    {"party": "Nimbus Labs India", "posting_date": "2026-07-02", "outstanding_amount": 142800},
                ],
                "truncated": False,
                "permission": {"allowed": True, "risk_level": "low", "confirmation_required": False},
            }
        payload = await frappe_reports.run_report(
            self.client,
            report_name,
            filters,
            cookies,
        )
        return normalize_report_result(self._unwrap(payload) or {})

    @staticmethod
    def _unwrap(payload: dict[str, Any]) -> Any:
        companion = payload.get("message", payload)
        if isinstance(companion, dict) and "success" in companion:
            return companion.get("data")
        return companion


async def default_report_filters(report_name: str, filters: dict[str, Any], erp: Any | None, cookies: dict | None = None) -> dict[str, Any]:
    output = dict(filters or {})
    if report_name == "Stock Balance":
        today = date.today()
        output.setdefault("from_date", today.replace(month=1, day=1).isoformat())
        output.setdefault("to_date", today.isoformat())
        if "company" not in output and erp is not None:
            try:
                context = await erp.get_current_user_context(cookies)
                if context.company:
                    output["company"] = context.company
            except Exception:
                pass
    return output


def normalize_report_result(result: dict[str, Any]) -> dict[str, Any]:
    columns = result.get("columns") or result.get("column") or []
    rows = result.get("rows")
    if rows is None:
        rows = result.get("result") or result.get("data") or []
    normalized_rows = [_row_to_dict(row, columns) for row in rows]
    return {**result, "columns": columns, "rows": normalized_rows, "result": normalized_rows, "permission": result.get("permission") or {"allowed": True, "risk_level": "low", "confirmation_required": False}}


def _row_to_dict(row: Any, columns: list[Any]) -> dict[str, Any]:
    if isinstance(row, dict):
        return row
    if isinstance(row, (list, tuple)):
        keys = []
        for index, column in enumerate(columns):
            if isinstance(column, dict):
                keys.append(column.get("fieldname") or column.get("key") or column.get("label") or f"col_{index}")
            else:
                keys.append(str(column).split(":")[0] or f"col_{index}")
        return {str(key): row[index] if index < len(row) else None for index, key in enumerate(keys)}
    return {"value": row}
