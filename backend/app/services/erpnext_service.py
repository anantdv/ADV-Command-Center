import json
from typing import Any

from app.config import settings
from app.core.exceptions import AppError
from app.db.seed import FULL_PERMISSION, INVOICES, MOCK_USER
from app.frappe import auth as frappe_auth
from app.frappe import crud as frappe_crud
from app.frappe import permissions as frappe_permissions
from app.frappe import schema as frappe_schema
from app.frappe.client import FrappeClient
from app.schemas.common import PermissionMeta
from app.schemas.erpnext import (
    AllowedDoctype,
    CurrentUserContext,
    DoctypeSchema,
    FieldSchema,
    ListRecordsResponse,
    RecordResponse,
)
from app.utils.filter_normalizer import FilterNormalizationError, normalize_filters, to_frappe_filters


class ERPNextService:
    """Frontend-facing ERP gateway backed exclusively by companion APIs in real mode."""

    def __init__(self, client: FrappeClient):
        self.client = client

    async def get_current_user_context(self, cookies: dict | None = None) -> CurrentUserContext:
        if settings.use_mock_data:
            return CurrentUserContext(
                **MOCK_USER,
                permissions=PermissionMeta(**FULL_PERMISSION),
            )
        data = self._unwrap(await frappe_auth.get_current_user_context(self.client, cookies))
        return CurrentUserContext(
            **data,
            permissions=PermissionMeta(can_read=True, allowed=not data.get("is_guest", False)),
        )

    async def get_allowed_doctypes(
        self,
        module: str | None = None,
        cookies: dict | None = None,
    ) -> list[AllowedDoctype]:
        if settings.use_mock_data:
            rows = [
                ("Sales Invoice", "Selling"),
                ("Customer", "Selling"),
                ("GL Entry", "Accounts"),
            ]
            if module:
                rows = [row for row in rows if row[1] == module]
            return [
                AllowedDoctype(
                    name=name,
                    label=name,
                    module=frappe_module,
                    permissions=PermissionMeta(**FULL_PERMISSION),
                )
                for name, frappe_module in rows
            ]
        data = self._unwrap(
            await frappe_permissions.get_allowed_doctypes(self.client, module, cookies)
        )
        return [
            AllowedDoctype(
                **item,
                permissions=PermissionMeta(can_read=True, allowed=True),
            )
            for item in data or []
        ]

    async def get_doctype_schema(
        self,
        doctype: str,
        cookies: dict | None = None,
    ) -> DoctypeSchema:
        if settings.use_mock_data:
            mock_fields = {
                "Customer": ["name", "customer_name", "customer_group", "territory", "disabled"],
                "Supplier": ["name", "supplier_name", "supplier_group", "disabled"],
                "Item": ["name", "item_name", "item_group", "stock_uom", "disabled"],
                "Sales Invoice": ["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status"],
                "Purchase Invoice": ["name", "supplier", "posting_date", "grand_total", "outstanding_amount", "status"],
                "Sales Order": ["name", "customer", "transaction_date", "grand_total", "status"],
                "Purchase Order": ["name", "supplier", "transaction_date", "grand_total", "status"],
            }.get(doctype, ["name", "status"])
            return DoctypeSchema(
                doctype=doctype,
                fields=[FieldSchema(fieldname=field, label=field.replace("_", " ").title(), fieldtype="Currency" if any(part in field for part in ("amount", "total")) else "Data", required=field == "name") for field in mock_fields],
                permissions=PermissionMeta(**FULL_PERMISSION),
            )
        data = self._unwrap(await frappe_schema.get_doctype_schema(self.client, doctype, cookies))
        fields = [
            FieldSchema(
                fieldname=field["fieldname"],
                label=field.get("label") or field["fieldname"],
                fieldtype=field.get("fieldtype") or "Data",
                options=field.get("options"),
                required=bool(field.get("reqd", field.get("required", False))),
                read_only=bool(field.get("read_only", False)),
                hidden=bool(field.get("hidden", False)),
                permlevel=int(field.get("permlevel") or 0),
            )
            for field in data.get("fields", [])
        ]
        return DoctypeSchema(
            doctype=data.get("doctype", doctype),
            module=data.get("module"),
            is_submittable=bool(data.get("is_submittable", False)),
            fields=fields,
            permissions=self._permission(data.get("permissions")),
        )

    async def list_records(
        self,
        doctype: str,
        filters: dict | list | None = None,
        fields: list[str] | None = None,
        limit: int = 20,
        order_by: str | None = None,
        cookies: dict | None = None,
        date_range: dict[str, Any] | None = None,
    ) -> ListRecordsResponse:
        try:
            filters = normalize_filters(doctype, filters or {}, date_range)
        except FilterNormalizationError as exc:
            raise AppError("I could not apply that filter safely. Please check the filter condition.", 422, {"doctype": doctype, "error": str(exc)}) from exc
        if settings.use_mock_data:
            records = self._mock_records(doctype, filters or {})
            return ListRecordsResponse(
                records=records[:limit],
                total=min(len(records), limit),
                permissions=PermissionMeta(**FULL_PERMISSION),
            )
        payload: dict[str, Any] = {
            "doctype": doctype,
            "filters": json.dumps(to_frappe_filters(doctype, filters or {})),
            "fields": fields or ["name"],
            "limit": min(max(limit, 1), 500),
        }
        if order_by:
            payload["order_by"] = order_by
        data = self._unwrap(await frappe_crud.list_records(self.client, payload, cookies))
        permission = self._permission(data.get("permission"))
        records = data.get("records") or []
        return ListRecordsResponse(
            records=records,
            total=int(data.get("count", len(records))),
            permissions=permission,
        )

    async def get_record(
        self,
        doctype: str,
        name: str,
        fields: list[str] | None = None,
        cookies: dict | None = None,
    ) -> RecordResponse:
        if settings.use_mock_data:
            record = next((item for item in self._mock_records(doctype, {}) if item.get("name") == name), None)
            if not record:
                record = {"doctype": doctype, "name": name, "status": "Draft", "docstatus": 0}
                if doctype == "Customer": record["territory"] = "Fiji"
            return RecordResponse(
                record={key:value for key,value in record.items() if not fields or key in {*fields,"name","docstatus"}},
                permissions=PermissionMeta(**FULL_PERMISSION),
            )
        payload = {"doctype": doctype, "name": name, "fields": fields or ["name"]}
        data = self._unwrap(await frappe_crud.get_record(self.client, payload, cookies))
        return RecordResponse(
            record=data.get("record") or {},
            permissions=self._permission(data.get("permission")),
        )

    async def create_record(
        self,
        doctype: str,
        data: dict,
        cookies: dict | None = None,
    ) -> RecordResponse:
        if settings.use_mock_data:
            return RecordResponse(
                record={"name": data.get("item_code") or data.get("customer_name") or data.get("supplier_name") or "NEW-0001", "docstatus": 0, "status": "Draft", **data},
                permissions=PermissionMeta(**FULL_PERMISSION),
            )
        result = self._unwrap(
            await frappe_crud.create_record(
                self.client,
                {"doctype": doctype, "data": data},
                cookies,
            )
        )
        permission = self._permission(result.get("permission"))
        return RecordResponse(record=self._record_payload(result), permissions=permission)

    async def check_permission(self, action: str, doctype: str, record_name: str | None = None, fields: list[str] | None = None, payload: dict | None = None, cookies: dict | None = None) -> PermissionMeta:
        if settings.use_mock_data:
            return PermissionMeta(**FULL_PERMISSION, confirmation_required=action in {"create", "update"}, risk_level="medium")
        request: dict[str, Any] = {"action":action,"doctype":doctype,"fields":fields or list((payload or {}).keys()),"payload":payload or {}}
        if record_name: request["record_name"] = record_name
        data = self._unwrap(await frappe_permissions.check_permission(self.client, request, cookies))
        return self._permission(data)

    async def update_record(
        self,
        doctype: str,
        name: str,
        data: dict,
        cookies: dict | None = None,
    ) -> RecordResponse:
        if settings.use_mock_data:
            return RecordResponse(
                record={"name": name, **data},
                permissions=PermissionMeta(**FULL_PERMISSION),
            )
        result = self._unwrap(
            await frappe_crud.update_record(
                self.client,
                {"doctype": doctype, "name": name, "data": data},
                cookies,
            )
        )
        permission = self._permission(result.get("permission"))
        return RecordResponse(record=self._record_payload(result), permissions=permission)

    @staticmethod
    def _unwrap(payload: dict[str, Any]) -> Any:
        companion = payload.get("message", payload)
        if isinstance(companion, dict) and "success" in companion:
            return companion.get("data")
        return companion

    @staticmethod
    def _permission(raw: dict | None) -> PermissionMeta:
        raw = raw or {}
        allowed = bool(raw.get("allowed", raw.get("can_read", True)))
        return PermissionMeta(
            allowed=allowed,
            can_read=bool(raw.get("can_read", allowed)),
            can_write=bool(raw.get("can_write", False)),
            can_create=bool(raw.get("can_create", False)),
            can_delete=bool(raw.get("can_delete", False)),
            can_submit=raw.get("can_submit"),
            can_cancel=raw.get("can_cancel"),
            can_export=raw.get("can_export"),
            reason=raw.get("reason"),
            filtered_fields=raw.get("filtered_fields") or [],
            blocked_fields=raw.get("blocked_fields") or [],
            confirmation_required=bool(raw.get("confirmation_required", False)),
            risk_level=raw.get("risk_level") or "low",
            audit_required=bool(raw.get("audit_required", True)),
        )

    @staticmethod
    def _record_payload(data: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value
            for key, value in data.items()
            if key not in {"permission", "blocked_fields"}
        } | ({"blocked_fields": data["blocked_fields"]} if data.get("blocked_fields") else {})

    @staticmethod
    def _mock_records(doctype: str, filters: dict | list) -> list[dict[str, Any]]:
        if doctype == "Sales Invoice" and isinstance(filters, dict) and filters.get("status") == "Overdue":
            return [
                {
                    "name": item["id"],
                    "customer": item["customer"],
                    "due_date": item["due"],
                    "grand_total": float(item["amount"].replace("₹", "").replace(",", "")),
                    "outstanding_amount": float(item["amount"].replace("₹", "").replace(",", "")),
                    "status": "Overdue",
                }
                for item in INVOICES
            ]
        fixtures = {
            "Customer": [
                {"name": "CUST-0001", "customer_name": "Aster Retail Pvt Ltd", "customer_group": "Commercial", "territory": "India", "disabled": 0},
                {"name": "CUST-0002", "customer_name": "Nimbus Labs India", "customer_group": "Commercial", "territory": "India", "disabled": 0},
            ],
            "Supplier": [{"name": "SUPP-0001", "supplier_name": "Acme Supplies", "supplier_group": "Local", "disabled": 0}],
            "Item": [
                {"name": "ITEM-001", "item_name": "Industrial Sensor", "item_group": "Products", "stock_uom": "Nos", "disabled": 0},
                {"name": "ITEM-002", "item_name": "Control Panel", "item_group": "Products", "stock_uom": "Nos", "disabled": 0},
            ],
            "Sales Invoice": [{"name": "SINV-2026-0418", "customer": "Aster Retail Pvt Ltd", "posting_date": "2026-07-01", "grand_total": 184500, "outstanding_amount": 184500, "status": "Overdue"}],
            "Purchase Invoice": [{"name": "PINV-2026-0101", "supplier": "Acme Supplies", "posting_date": "2026-07-01", "grand_total": 82500, "outstanding_amount": 20000, "status": "Unpaid"}],
            "Sales Order": [{"name": "SAL-ORD-2026-0001", "customer": "Aster Retail Pvt Ltd", "transaction_date": "2026-07-01", "grand_total": 225000, "status": "To Deliver and Bill"}],
            "Purchase Order": [{"name": "PUR-ORD-2026-0001", "supplier": "Acme Supplies", "transaction_date": "2026-07-01", "grand_total": 125000, "status": "To Receive and Bill"}],
        }
        return fixtures.get(doctype, [{"name": f"{doctype}-0001", "status": "Open"}])
