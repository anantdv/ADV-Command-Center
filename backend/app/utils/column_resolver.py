from __future__ import annotations

from typing import Any

from app.core.exceptions import AppError
from app.frappe.client import FrappeClient
from app.schemas.report_builder import ReportColumn
from app.services.erpnext_service import ERPNextService
from app.services.report_service import ReportService

SENSITIVE_FIELD_PARTS = ("password", "secret", "token", "api_key", "api_secret", "otp", "bank", "account_no", "salary", "pan", "aadhaar")
TECHNICAL_FIELDS = {"owner", "modified_by", "creation", "modified", "docstatus", "idx"}


class ColumnResolver:
    def __init__(self, client: FrappeClient):
        self.erp = ERPNextService(client)
        self.reports = ReportService(client)

    async def get_available_columns(self, source_type: str, source_name: str, cookies: dict | None = None) -> list[ReportColumn]:
        if source_type == "doctype":
            schema = await self.erp.get_doctype_schema(source_name, cookies)
            return [
                ReportColumn(key=field.fieldname, label=field.label or field.fieldname.replace("_", " ").title(), fieldtype=field.fieldtype, source="doctype")
                for field in schema.fields
                if not field.hidden and field.fieldname not in TECHNICAL_FIELDS and not _sensitive(field.fieldname)
            ]
        if source_type == "report":
            sample = await self.reports.run_report(source_name, {}, cookies)
            columns = sample.get("columns") or []
            return [_report_column(column) for column in columns if not _sensitive(_column_key(column))]
        raise AppError("source_type must be doctype or report", 422)

    async def validate_selected_columns(self, source_type: str, source_name: str, selected_columns: list[str], cookies: dict | None = None) -> list[str]:
        available = await self.get_available_columns(source_type, source_name, cookies)
        allowed = {column.key for column in available}
        selected = selected_columns or [column.key for column in available[:12]]
        invalid = [column for column in selected if column not in allowed or _sensitive(column)]
        if invalid:
            raise AppError("One or more selected columns are not available or not allowed.", 422, {"invalid_columns": invalid})
        return selected


def _sensitive(value: str) -> bool:
    lowered = value.lower()
    return any(part in lowered for part in SENSITIVE_FIELD_PARTS)


def _column_key(column: Any) -> str:
    if isinstance(column, str):
        return column.split(":")[0]
    if isinstance(column, dict):
        return str(column.get("fieldname") or column.get("key") or column.get("label") or "")
    return str(column)


def _report_column(column: Any) -> ReportColumn:
    key = _column_key(column)
    if isinstance(column, dict):
        return ReportColumn(key=key, label=str(column.get("label") or key.replace("_", " ").title()), fieldtype=str(column.get("fieldtype") or "Data"), source="report")
    label = key.replace("_", " ").title()
    return ReportColumn(key=key, label=label, source="report")
