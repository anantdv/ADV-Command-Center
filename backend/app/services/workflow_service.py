from __future__ import annotations

from typing import Any

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError, PermissionDenied
from app.frappe.client import FrappeClient
from app.frappe.paths import APPLY_WORKFLOW_ACTION, GET_AVAILABLE_WORKFLOW_ACTIONS, GET_PENDING_WORKFLOW_DOCUMENTS, GET_WORKFLOW_DOCUMENT_DETAIL, WORKFLOW_DEBUG
from app.schemas.workflow import ApplyWorkflowActionRequest, ApplyWorkflowActionResponse, PendingApprovalsResponse, PendingWorkflowDocument, WorkflowAction, WorkflowDocumentDetail


class WorkflowService:
    """FastAPI facade for ERPNext/Frappe workflow actions.

    This service intentionally does not implement its own approval engine. In
    real mode every operation delegates to the Frappe companion app, which must
    use the logged-in user's permissions and Frappe workflow transitions.
    """

    def __init__(self, client: FrappeClient | None = None):
        self.client = client or FrappeClient(settings.frappe_base_url, settings.frappe_auth_mode, settings.frappe_api_key, settings.frappe_api_secret, settings.frappe_session_cookie_name)

    async def list_pending_approvals(self, doctype: str | None = None, cookies: dict | None = None, limit: int = 50, user: str = "unknown") -> PendingApprovalsResponse:
        limit = min(max(limit or settings.workflow_approval_limit, 1), settings.workflow_approval_limit)
        if settings.use_mock_data:
            docs = [doc for doc in _mock_pending() if not doctype or doc.doctype == doctype][:limit]
            await self._audit("workflow_pending_approvals_viewed", user, doctype=doctype, allowed=True, output=f"{len(docs)} documents")
            return PendingApprovalsResponse(documents=docs, total=len(docs), filters={"doctype": doctype} if doctype else {})
        data = self._unwrap(await self.client.get(GET_PENDING_WORKFLOW_DOCUMENTS, {"doctype": doctype, "limit": limit}, cookies))
        docs = [PendingWorkflowDocument.model_validate(item) for item in (data.get("documents") if isinstance(data, dict) else data) or []]
        await self._audit("workflow_pending_approvals_viewed", user, doctype=doctype, allowed=True, output=f"{len(docs)} documents")
        return PendingApprovalsResponse(documents=docs, total=int((data or {}).get("total", len(docs))) if isinstance(data, dict) else len(docs), filters=(data or {}).get("filters", {"doctype": doctype} if doctype else {}) if isinstance(data, dict) else {})

    async def get_document_detail(self, doctype: str, name: str, cookies: dict | None = None, user: str = "unknown") -> WorkflowDocumentDetail:
        if settings.use_mock_data:
            doc = next((item for item in _mock_pending() if item.doctype == doctype and item.name == name), None)
            if not doc:
                raise AppError("Workflow document was not found.", 404, {"doctype": doctype, "name": name})
            detail = WorkflowDocumentDetail(doctype=doctype, name=name, title=doc.title, workflow_state=doc.workflow_state, status=doc.status, docstatus=0, summary={"party": doc.party, "grand_total": doc.grand_total, "currency": doc.currency}, fields={"name": name, "workflow_state": doc.workflow_state, "status": doc.status}, items=[], available_actions=doc.available_actions, permission={"allowed": True, "risk_level": "low"})
            await self._audit("workflow_document_detail_viewed", user, doctype, name, True)
            return detail
        data = self._unwrap(await self.client.get(GET_WORKFLOW_DOCUMENT_DETAIL, {"doctype": doctype, "name": name}, cookies))
        detail = WorkflowDocumentDetail.model_validate(data)
        await self._audit("workflow_document_detail_viewed", user, doctype, name, True)
        return detail

    async def get_available_actions(self, doctype: str, name: str, cookies: dict | None = None, user: str = "unknown") -> list[WorkflowAction]:
        detail = await self.get_document_detail(doctype, name, cookies, user)
        await self._audit("workflow_actions_loaded", user, doctype, name, True)
        return detail.available_actions

    async def debug(self, doctype: str | None = None, cookies: dict | None = None, limit: int = 50, user: str = "unknown") -> dict[str, Any]:
        if settings.use_mock_data:
            docs = _mock_pending()[:limit]
            return {
                "session_user": user,
                "workflow_actions_found": len(docs),
                "after_permission_filter": len(docs),
                "after_transition_filter": len(docs),
                "records": [doc.model_dump(mode="json") for doc in docs if not doctype or doc.doctype == doctype],
            }
        data = self._unwrap(await self.client.get(WORKFLOW_DEBUG, {"doctype": doctype, "limit": limit}, cookies))
        await self._audit("workflow_debug_viewed", user, doctype=doctype, allowed=True, output=f"{data.get('after_transition_filter', 0) if isinstance(data, dict) else 0} documents")
        return data if isinstance(data, dict) else {"records": data}

    async def apply_action(self, request: ApplyWorkflowActionRequest, cookies: dict | None = None, user: str = "unknown") -> ApplyWorkflowActionResponse:
        if settings.use_mock_data:
            detail = await self.get_document_detail(request.doctype, request.name, cookies, user)
            if request.action not in {action.action for action in detail.available_actions}:
                await self._audit("workflow_action_not_available", user, request.doctype, request.name, False, action=request.action)
                raise PermissionDenied("This workflow action is not available for your user on this document.")
            next_state = next((action.next_state for action in detail.available_actions if action.action == request.action), None)
            response = ApplyWorkflowActionResponse(doctype=request.doctype, name=request.name, action=request.action, previous_state=detail.workflow_state, new_state=next_state or "Actioned", status="Workflow Action Applied", message=f'ERPNext workflow action "{request.action}" applied.', result={"comment_present": bool(request.comment)})
            await self._audit("workflow_action_applied", user, request.doctype, request.name, True, action=request.action, output=f"{detail.workflow_state}->{response.new_state}")
            return response
        payload = request.model_dump(exclude_none=True)
        try:
            data = self._unwrap(await self.client.post(APPLY_WORKFLOW_ACTION, payload, cookies))
            response = ApplyWorkflowActionResponse.model_validate(data)
            await self._audit("workflow_action_applied", user, request.doctype, request.name, True, action=request.action, output=f"{response.previous_state}->{response.new_state}")
            return response
        except Exception as exc:
            await self._audit("workflow_action_failed", user, request.doctype, request.name, False, action=request.action, output=type(exc).__name__)
            raise

    @staticmethod
    def _unwrap(payload: dict[str, Any]) -> Any:
        companion = payload.get("message", payload)
        if isinstance(companion, dict) and "success" in companion:
            if companion.get("success") is False:
                raise AppError(companion.get("message") or "Workflow request failed.", 400, companion.get("details") or {})
            return companion.get("data")
        return companion

    @staticmethod
    async def _audit(action_name: str, user: str, doctype: str | None = None, name: str | None = None, allowed: bool = True, action: str | None = None, output: str | None = None) -> None:
        await log_audit_event(AuditEvent(user=user, action=action_name, agent_name="workflow_agent", tool_name="erpnext_workflow", doctype=doctype, record_name=name, allowed=allowed, risk_level="medium" if "action" in action_name else "low", input_summary=action, output_summary=output, erp_data_sent=False))


def _mock_pending() -> list[PendingWorkflowDocument]:
    return [
        PendingWorkflowDocument(doctype="Sales Invoice", name="ACC-SINV-2025-00001", title="Sales Invoice ACC-SINV-2025-00001", workflow_state="Pending Approval", status="Pending", posting_date="2025-05-15", party="ABC Trading", grand_total=52500, currency="INR", available_actions=[WorkflowAction(action="Approve", next_state="Approved"), WorkflowAction(action="Reject", next_state="Rejected")]),
        PendingWorkflowDocument(doctype="Purchase Order", name="PUR-ORD-2025-00007", title="Purchase Order PUR-ORD-2025-00007", workflow_state="Pending Approval", status="Pending", transaction_date="2025-05-20", party="Pacific Hardware", grand_total=47500, currency="INR", available_actions=[WorkflowAction(action="Approve", next_state="Approved"), WorkflowAction(action="Reject", next_state="Rejected")]),
    ]


workflow_service = WorkflowService()
