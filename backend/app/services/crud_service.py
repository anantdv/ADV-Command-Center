from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError, PermissionDenied
from app.frappe.client import FrappeClient
from app.schemas.crud import ConfirmCrudResponse, CrudPreviewResponse, MissingField
from app.services.erpnext_service import ERPNextService
from app.utils.confirmation_store import ConfirmationStore, confirmation_store
from app.utils.doctype_defaults import apply_document_defaults
from app.utils.field_mapper import ALLOWED_CREATE_FIELDS, ALLOWED_UPDATE_FIELDS, FIELD_LABELS, FIELD_OPTIONS, filter_write_data, missing_required_fields
from app.utils.item_table_builder import item_warnings, normalize_items_for_doctype, strip_internal_item_markers


class CrudService:
    """Prepares and executes narrowly allowlisted writes through the Frappe companion app."""
    def __init__(self, erp: ERPNextService | None = None, confirmations: ConfirmationStore | None = None):
        self.erp = erp or ERPNextService(FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name))
        self.confirmations = confirmations or confirmation_store

    async def prepare_create(self, doctype: str, data: dict, conversation_id: str | None = None, message_id: str | None = None, cookies: dict | None = None, user: str = "unknown") -> CrudPreviewResponse:
        if doctype not in ALLOWED_CREATE_FIELDS: raise AppError(f"Creating {doctype} is not enabled in this stage.", 422)
        data = self._pre_normalize_create_data(doctype, data)
        filtered, blocked = filter_write_data(doctype, "create", data)
        if blocked: raise AppError("One or more fields are not allowed for draft creation.", 422, {"blocked_fields":blocked})
        warnings: list[str] = []
        if "items" in filtered:
            filtered["items"] = normalize_items_for_doctype(doctype, filtered.get("items") or [])
            warnings.extend(item_warnings(filtered["items"]))
            filtered["items"] = strip_internal_item_markers(filtered["items"])
        try:
            user_context = (await self.erp.get_current_user_context(cookies)).model_dump()
        except Exception:
            user_context = None
        filtered = apply_document_defaults(doctype, filtered, user_context)
        filtered.pop("docstatus", None)
        missing = self._missing(doctype, filtered)
        if missing:
            await self._audit("crud_missing_fields", user, "create", doctype, None, filtered, [], conversation_id=conversation_id, status="missing_fields")
            return CrudPreviewResponse(operation="create", doctype=doctype, data=filtered, missing_fields=missing, confirmation_required=False, warnings=warnings)
        permission = await self.erp.check_permission("create", doctype, fields=list(filtered), payload=filtered, cookies=cookies)
        if not permission.allowed:
            await self._audit("crud_permission_denied", user, "create", doctype, None, filtered, permission.blocked_fields, conversation_id=conversation_id, status="denied")
            raise PermissionDenied(permission.reason or f"You do not have permission to create {doctype}.")
        confirmation_id = self.confirmations.create({"operation":"create","doctype":doctype,"record_name":None,"data":filtered,"user":user,"conversation_id":conversation_id,"message_id":message_id})
        await self._audit("crud_confirmation_created", user, "create", doctype, None, filtered, [], confirmation_id, conversation_id, "pending")
        return CrudPreviewResponse(operation="create", doctype=doctype, data=filtered, after_data=filtered, permission=permission.model_dump(), confirmation_id=confirmation_id, warnings=warnings)

    @staticmethod
    def _pre_normalize_create_data(doctype: str, data: dict[str, Any]) -> dict[str, Any]:
        output = dict(data or {})
        warehouse = output.pop("warehouse", None)
        if warehouse and isinstance(output.get("items"), list):
            output["items"] = [{**item, "warehouse": item.get("warehouse") or warehouse} for item in output["items"] if isinstance(item, dict)]
        if doctype == "Stock Entry" and output.get("stock_entry_type", "").lower() == "material transfer":
            output.setdefault("purpose", "Material Transfer")
        if doctype == "Journal Entry":
            output.setdefault("voucher_type", "Journal Entry")
        return output

    async def prepare_update(self, doctype: str, record_name: str, data: dict, conversation_id: str | None = None, message_id: str | None = None, cookies: dict | None = None, user: str = "unknown") -> CrudPreviewResponse:
        if doctype not in ALLOWED_UPDATE_FIELDS: raise AppError(f"Updating {doctype} is not enabled in this stage.", 422)
        if not record_name: raise AppError("Record name is required for an update.", 422)
        filtered, blocked = filter_write_data(doctype, "update", data)
        if blocked: raise AppError("One or more fields are not allowed for update.", 422, {"blocked_fields":blocked})
        if not filtered: raise AppError("No safe update fields were provided.", 422)
        current = await self.erp.get_record(doctype, record_name, [*filtered.keys(), "docstatus", "status"], cookies)
        if doctype == "Quotation" and int(current.record.get("docstatus", 0) or 0) != 0: raise AppError("Only Draft Quotations can be updated.", 409)
        permission = await self.erp.check_permission("update", doctype, record_name, list(filtered), filtered, cookies)
        if not permission.allowed:
            await self._audit("crud_permission_denied", user, "update", doctype, record_name, filtered, permission.blocked_fields, conversation_id=conversation_id, status="denied")
            raise PermissionDenied(permission.reason or f"You do not have permission to update {doctype}.")
        before = {field:current.record.get(field) for field in filtered}
        after = {**before, **filtered}
        confirmation_id = self.confirmations.create({"operation":"update","doctype":doctype,"record_name":record_name,"data":filtered,"before_data":before,"user":user,"conversation_id":conversation_id,"message_id":message_id})
        await self._audit("crud_confirmation_created", user, "update", doctype, record_name, filtered, [], confirmation_id, conversation_id, "pending")
        return CrudPreviewResponse(operation="update", doctype=doctype, record_name=record_name, data=filtered, before_data=before, after_data=after, permission=permission.model_dump(), confirmation_id=confirmation_id)

    async def confirm(self, confirmation_id: str, cookies: dict | None = None, user: str = "unknown") -> ConfirmCrudResponse:
        pending = self.confirmations.get(confirmation_id)
        if not pending: raise AppError("Confirmation is invalid, expired, or has already been used.", 410)
        if pending["user"] != user: raise PermissionDenied("This confirmation belongs to a different user.")
        # Consume only after ownership has been verified. This prevents another
        # user from invalidating a confirmation token they do not own.
        item = self.confirmations.consume(confirmation_id)
        if not item: raise AppError("Confirmation is invalid, expired, or has already been used.", 410)
        operation, doctype, record_name, data = item["operation"], item["doctype"], item.get("record_name"), item["data"]
        try:
            permission = await self.erp.check_permission(operation, doctype, record_name, list(data), data, cookies)
            if not permission.allowed: raise PermissionDenied(permission.reason or "ERPNext permission denied.")
            await self._audit("crud_confirmed", user, operation, doctype, record_name, data, permission.blocked_fields, confirmation_id, item.get("conversation_id"), "confirmed")
            if operation == "create": result = await self.erp.create_record(doctype, data, cookies)
            else:
                if doctype == "Quotation":
                    current = await self.erp.get_record(doctype, record_name, ["docstatus"], cookies)
                    if int(current.record.get("docstatus", 0) or 0) != 0: raise AppError("Only Draft Quotations can be updated.", 409)
                result = await self.erp.update_record(doctype, record_name, data, cookies)
            name = str(result.record.get("name") or record_name or "Draft")
            status = str(result.record.get("status") or ("Created" if operation == "create" else "Updated"))
            action = "crud_create_success" if operation == "create" else "crud_update_success"
            await self._audit(action, user, operation, doctype, name, data, result.permissions.blocked_fields, confirmation_id, item.get("conversation_id"), status)
            verb = "created" if operation == "create" else "updated"
            return ConfirmCrudResponse(operation=operation, doctype=doctype, record_name=name, status=status, message=f"{doctype} {name} has been {verb} successfully.", data=result.record)
        except Exception:
            await self._audit("crud_create_failed" if operation == "create" else "crud_update_failed", user, operation, doctype, record_name, data, [], confirmation_id, item.get("conversation_id"), "failed")
            raise

    async def cancel(self, confirmation_id: str, user: str = "unknown") -> bool:
        item = self.confirmations.get(confirmation_id)
        if not item: raise AppError("Confirmation is invalid or expired.", 410)
        if item["user"] != user: raise PermissionDenied("This confirmation belongs to a different user.")
        cancelled = self.confirmations.cancel(confirmation_id)
        if cancelled: await self._audit("crud_cancelled", user, item["operation"], item["doctype"], item.get("record_name"), item["data"], [], confirmation_id, item.get("conversation_id"), "cancelled")
        return cancelled

    @staticmethod
    def _missing(doctype: str, data: dict[str, Any]) -> list[MissingField]:
        output=[]
        for field in missing_required_fields(doctype, data):
            fieldtype = "Table" if field == "items" else "Select" if FIELD_OPTIONS.get(field) else "Data"
            output.append(MissingField(fieldname=field,label=FIELD_LABELS.get(field,field.replace("_"," ").title()),fieldtype=fieldtype,options=FIELD_OPTIONS.get(field)))
        return output

    @staticmethod
    async def _audit(action: str, user: str, operation: str, doctype: str, record_name: str | None, data: dict, blocked: list[str], confirmation_id: str | None = None, conversation_id: str | None = None, status: str | None = None) -> None:
        await log_audit_event(AuditEvent(user=user,conversation_id=conversation_id,action=action,agent_name="crud_agent",tool_name=f"{operation}_draft",doctype=doctype,record_name=record_name,allowed=action not in {"crud_permission_denied","crud_create_failed","crud_update_failed"},risk_level="medium",input_summary=f"{operation} {doctype}; fields={','.join(data.keys())}",output_summary=status,operation=operation,allowed_fields=list(data),blocked_fields=blocked,confirmation_id=confirmation_id,status=status))


crud_service = CrudService()
