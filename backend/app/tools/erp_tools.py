from typing import Any

from app.config import settings
from app.frappe.client import FrappeClient
from app.schemas.chat import PermissionMeta, SourceMeta
from app.services.erpnext_service import ERPNextService
from app.utils.field_alias_mapper import DEFAULT_FIELDS
from app.utils.filter_normalizer import normalize_filters


class ERPReadTools:
    def __init__(self, service: ERPNextService | None = None):
        self.service = service or ERPNextService(
            FrappeClient(
                settings.frappe_base_url,
                settings.frappe_auth_mode,
                settings.frappe_api_key,
                settings.frappe_api_secret,
                settings.frappe_session_cookie_name,
            )
        )

    async def list_records(
        self,
        doctype: str,
        filters: dict | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        order_by: str | None = None,
        cookies: dict | None = None,
        date_range: dict | None = None,
    ) -> dict[str, Any]:
        requested_fields = fields or DEFAULT_FIELDS.get(doctype, ["name"])
        normalized_filters = normalize_filters(doctype, filters or {}, date_range)
        result = await self.service.list_records(
            doctype=doctype,
            filters=normalized_filters,
            fields=requested_fields,
            limit=min(limit, 20),
            order_by=order_by,
            cookies=cookies,
            date_range=None,
        )
        columns = list(result.records[0].keys()) if result.records else requested_fields
        return {
            "records": result.records,
            "columns": columns,
            "record_count": result.total,
            "source": SourceMeta(
                source_type="doctype",
                source_name=doctype,
                record_count=result.total,
                filters=normalized_filters,
                doctype=doctype,
                fields=requested_fields,
            ).model_dump(),
            "permission": self._permission(result.permissions).model_dump(),
        }

    async def get_record(
        self,
        doctype: str,
        name: str,
        fields: list[str] | None = None,
        cookies: dict | None = None,
    ) -> dict[str, Any]:
        requested_fields = fields or DEFAULT_FIELDS.get(doctype, ["name"])
        result = await self.service.get_record(
            doctype=doctype,
            name=name,
            fields=requested_fields,
            cookies=cookies,
        )
        record_count = 1 if result.record else 0
        return {
            "records": [result.record] if result.record else [],
            "columns": list(result.record.keys()) if result.record else requested_fields,
            "record_count": record_count,
            "source": SourceMeta(
                source_type="doctype",
                source_name=doctype,
                record_count=record_count,
                filters={"name": name},
                doctype=doctype,
                fields=requested_fields,
            ).model_dump(),
            "permission": self._permission(result.permissions).model_dump(),
        }

    async def get_document_detail(
        self,
        doctype: str,
        name: str,
        cookies: dict | None = None,
    ) -> dict[str, Any]:
        result = await self.service.get_document_detail(doctype=doctype, name=name, cookies=cookies)
        return {
            "detail": result.model_dump(mode="json"),
            "record_count": 1,
            "source": SourceMeta(
                source_type="doctype",
                source_name=doctype,
                record_count=1,
                filters={"name": name},
                doctype=doctype,
            ).model_dump(),
            "permission": result.permission or PermissionMeta(allowed=True).model_dump(),
        }

    @staticmethod
    def _permission(permission: Any) -> PermissionMeta:
        return PermissionMeta(
            allowed=permission.allowed,
            risk_level=permission.risk_level if permission.risk_level in {"low", "medium", "high"} else "low",
            confirmation_required=permission.confirmation_required,
            filtered_fields=permission.filtered_fields,
            blocked_fields=permission.blocked_fields,
            reason=permission.reason,
        )


ERP_TOOL_NAMES = ["list_records", "get_record", "get_document_detail"]
