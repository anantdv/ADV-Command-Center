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
    DocumentDetailResponse,
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
                "Sales Invoice": ["name", "customer", "posting_date", "grand_total", "outstanding_amount", "status", "items"],
                "Purchase Invoice": ["name", "supplier", "posting_date", "grand_total", "outstanding_amount", "status", "items"],
                "Sales Order": ["name", "customer", "transaction_date", "grand_total", "status", "items"],
                "Purchase Order": ["name", "supplier", "transaction_date", "grand_total", "status", "items"],
                "Sales Invoice Item": ["name", "item_code", "item_name", "qty", "rate", "amount"],
                "Purchase Invoice Item": ["name", "item_code", "item_name", "qty", "rate", "amount"],
                "Sales Order Item": ["name", "item_code", "item_name", "qty", "rate", "amount", "warehouse"],
                "Purchase Order Item": ["name", "item_code", "item_name", "qty", "rate", "amount", "warehouse"],
            }.get(doctype, ["name", "status"])
            link_options = {
                "customer": "Customer",
                "supplier": "Supplier",
                "item_code": "Item",
                "warehouse": "Warehouse",
            }
            table_options = {
                "Sales Invoice": "Sales Invoice Item",
                "Purchase Invoice": "Purchase Invoice Item",
                "Sales Order": "Sales Order Item",
                "Purchase Order": "Purchase Order Item",
            }
            return DoctypeSchema(
                doctype=doctype,
                fields=[
                    FieldSchema(
                        fieldname=field,
                        label=field.replace("_", " ").title(),
                        fieldtype="Table" if field == "items" else "Link" if field in link_options else "Currency" if any(part in field for part in ("amount", "total", "rate")) else "Float" if field == "qty" else "Data",
                        options=table_options.get(doctype) if field == "items" else link_options.get(field),
                        required=field == "name",
                    )
                    for field in mock_fields
                ],
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
                depends_on=field.get("depends_on"),
                fetch_from=field.get("fetch_from"),
                default=field.get("default"),
                description=field.get("description") or field.get("help"),
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
            records = self._apply_mock_filters(self._mock_records(doctype, filters or {}), filters or {})
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

    async def get_document_detail(
        self,
        doctype: str,
        name: str,
        cookies: dict | None = None,
    ) -> DocumentDetailResponse:
        if settings.use_mock_data:
            record = next((item for item in self._mock_records(doctype, {}) if item.get("name") == name), None)
            if not record:
                record = {"name": name, "status": "Draft", "docstatus": 0}
                if doctype == "Sales Invoice":
                    record |= {"customer": "Aster Retail Pvt Ltd", "posting_date": "2026-07-01", "grand_total": 184500, "outstanding_amount": 184500, "currency": "INR"}
                    record["items"] = [{"name": f"{name}-1", "item_code": "ITEM-001", "item_name": "Industrial Sensor", "qty": 2, "rate": 5000, "amount": 10000}]
                elif doctype == "Purchase Order":
                    record |= {"supplier": "Acme Supplies", "transaction_date": "2026-07-01", "grand_total": 125000, "currency": "INR"}
                    record["items"] = [{"name": f"{name}-1", "item_code": "ITEM-001", "item_name": "Industrial Sensor", "qty": 1, "rate": 125000, "amount": 125000}]
                elif doctype == "Customer":
                    record |= {"customer_name": name, "customer_group": "Commercial", "territory": "India"}
                elif doctype == "Item":
                    record |= {"item_name": name, "item_group": "Products", "stock_uom": "Nos"}
            if doctype == "Sales Invoice" and not record.get("items"):
                record["items"] = [{"name": f"{name}-1", "item_code": "ITEM-001", "item_name": "Industrial Sensor", "qty": 2, "rate": 5000, "amount": 10000}]
            if doctype == "Purchase Order" and not record.get("items"):
                record["items"] = [{"name": f"{name}-1", "item_code": "ITEM-001", "item_name": "Industrial Sensor", "qty": 1, "rate": record.get("grand_total") or 125000, "amount": record.get("grand_total") or 125000}]
            summary_keys = [
                "customer", "supplier", "party_name", "customer_name", "supplier_name", "item_name",
                "posting_date", "transaction_date", "grand_total", "outstanding_amount", "currency",
            ]
            workflow_actions = []
            if doctype in {"Sales Invoice", "Purchase Order"} and (record.get("status") in {None, "Draft", "Pending", "Pending Approval"}):
                workflow_actions = [{"action": "Approve", "next_state": "Approved"}, {"action": "Reject", "next_state": "Rejected"}]
                record.setdefault("workflow_state", "Pending Approval")
            return DocumentDetailResponse(
                doctype=doctype,
                name=name,
                title=f"{doctype} {name}",
                docstatus=int(record.get("docstatus") or 0),
                status=record.get("status"),
                workflow_state=record.get("workflow_state"),
                summary={key: record[key] for key in summary_keys if key in record},
                fields=record,
                items=record.get("items") or [],
                available_workflow_actions=workflow_actions,
                permission=FULL_PERMISSION,
            )
        data = self._unwrap(
            await frappe_crud.get_document_detail(
                self.client,
                {"doctype": doctype, "name": name},
                cookies,
            )
        )
        return DocumentDetailResponse(
            doctype=data.get("doctype", doctype),
            name=data.get("name", name),
            title=data.get("title") or data.get("name", name),
            docstatus=data.get("docstatus"),
            status=data.get("status"),
            workflow_state=data.get("workflow_state"),
            summary=data.get("summary") or {},
            fields=data.get("fields") or {},
            items=data.get("items") or [],
            available_workflow_actions=data.get("available_workflow_actions") or data.get("available_actions") or [],
            permission=data.get("permission"),
        )

    async def search_link(
        self,
        doctype: str,
        txt: str,
        cookies: dict | None = None,
        limit: int = 10,
    ) -> list[dict[str, str]]:
        field = {"Supplier": "supplier_name", "Customer": "customer_name", "Item": "item_name"}.get(doctype, "name")
        if settings.use_mock_data:
            rows = self._mock_records(doctype, {})
        else:
            rows = (await self.list_records(doctype, {}, ["name", field], min(limit * 5, 100), cookies=cookies)).records
        needle = (txt or "").lower()
        matches = []
        for row in rows:
            name = str(row.get("name") or "")
            label = str(row.get(field) or name)
            if not needle or needle in name.lower() or needle in label.lower():
                display = f"{name} - {label}" if doctype == "Item" and label and label != name else label
                description = str(row.get("stock_uom") or doctype) if doctype == "Item" else doctype
                matches.append({"name": name, "label": display, "description": description})
            if len(matches) >= limit:
                break
        return matches

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
                {"name": "CUST-00045", "customer_name": "Biswajit Maity", "customer_group": "Individual", "territory": "India", "mobile_no": "9999999999", "email_id": "biswajit@example.com", "disabled": 0},
            ],
            "Supplier": [
                {"name": "SUPP-0001", "supplier_name": "Acme Supplies", "supplier_group": "Local", "disabled": 0},
                {"name": "001463", "supplier_name": "ZUCCI MODE LTD", "supplier_group": "Local", "disabled": 0},
                {"name": "SUP-2026-00010", "supplier_name": "BNBM Kokopo", "supplier_group": "Local", "disabled": 0},
            ],
            "Item": [
                {"name": "ITEM-001", "item_name": "Industrial Sensor", "item_group": "Products", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "TCL-FRIDGE-TM-001", "item_name": "TCL Top Mount Fridge", "description": "TCL top mount refrigerator", "item_group": "Refrigerators", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "AIR-FRYER-001", "item_name": "Air Fryer", "description": "Electric air fryer", "item_group": "Appliances", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "TV-32-SMART", "item_name": "32 Inch Smart TV", "description": "32-inch LED Smart Television", "item_group": "Television", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "KA-HBEO4-00087", "item_name": "Home Basics Electric Oven 45L", "description": "Electric oven 45L", "item_group": "Appliances", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "HA-MSA1-00045", "item_name": "Midea Split AC 18000BTU", "description": "Midea split air conditioner", "brand": "Midea", "item_group": "Air Conditioners", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "MD-SPLIT-AC-001", "item_name": "Midea Split AC", "description": "Midea split air conditioner", "brand": "Midea", "item_group": "Air Conditioners", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "MD-SPLIT-AC-002", "item_name": "Midea Split AC 2 Ton", "description": "Midea split air conditioner 2 ton", "brand": "Midea", "item_group": "Air Conditioners", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
                {"name": "ITEM-002", "item_name": "Control Panel", "item_group": "Products", "stock_uom": "Nos", "disabled": 0, "is_stock_item": 1},
            ],
            "Warehouse": [
                {"name": "Stores - CTS", "warehouse_name": "Stores", "company": "Courts", "is_group": 0, "disabled": 0},
                {"name": "POM Warehouse - CTS", "warehouse_name": "POM Warehouse", "company": "Courts", "is_group": 0, "disabled": 0},
                {"name": "Goods In Transit - CTS", "warehouse_name": "Goods In Transit", "company": "Courts", "is_group": 0, "disabled": 0},
                {"name": "All Warehouses - CTS", "warehouse_name": "All Warehouses", "company": "Courts", "is_group": 1, "disabled": 0},
            ],
            "Sales Invoice": [{"name": "SINV-2026-0418", "customer": "Aster Retail Pvt Ltd", "posting_date": "2026-07-01", "grand_total": 184500, "outstanding_amount": 184500, "status": "Overdue"}],
            "Purchase Invoice": [{"name": "PINV-2026-0101", "supplier": "Acme Supplies", "posting_date": "2026-07-01", "grand_total": 82500, "outstanding_amount": 20000, "status": "Unpaid"}],
            "Sales Order": [{"name": "SAL-ORD-2026-0001", "customer": "Aster Retail Pvt Ltd", "transaction_date": "2026-07-01", "grand_total": 225000, "status": "To Deliver and Bill"}],
            "Purchase Order": [
                {"name": "PUR-ORD-2026-0001", "supplier": "Acme Supplies", "transaction_date": "2026-07-01", "grand_total": 125000, "status": "To Receive and Bill", "docstatus": 1, "per_received": 0, "per_billed": 0},
                {"name": "PUR-ORD-2026-00624", "supplier": "SUP-2026-00010", "supplier_name": "BNBM Kokopo", "transaction_date": "2026-07-20", "grand_total": 1500, "status": "Draft", "docstatus": 0, "per_received": 0, "per_billed": 0},
            ],
        }
        return fixtures.get(doctype, [{"name": f"{doctype}-0001", "status": "Open"}])

    @staticmethod
    def _apply_mock_filters(records: list[dict[str, Any]], filters: dict | list) -> list[dict[str, Any]]:
        if not isinstance(filters, dict) or not filters:
            return records
        return [
            record
            for record in records
            if all(ERPNextService._mock_match(record, field, value) for field, value in filters.items() if not str(field).startswith("_"))
        ]

    @staticmethod
    def _mock_match(record: dict[str, Any], field: str, value: Any) -> bool:
        actual = record.get(field)
        if isinstance(value, list) and len(value) == 2:
            op = str(value[0]).lower()
            target = value[1]
            if op == "like":
                return str(target).strip("%").lower() in str(actual or "").lower()
            if op == "in":
                return actual in target
            if op == "not in":
                return actual not in target
            if op == "<":
                return float(actual or 0) < float(target)
            if op == ">":
                return float(actual or 0) > float(target)
            if op == "=":
                return actual == target
        return actual == value
