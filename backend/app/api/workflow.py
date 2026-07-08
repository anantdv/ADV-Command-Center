from __future__ import annotations

from fastapi import APIRouter, Query, Request

from app.dependencies import CurrentUserDep, get_frappe_client, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.workflow import ApplyWorkflowActionRequest, ApplyWorkflowActionResponse, PendingApprovalsResponse, WorkflowAction, WorkflowDocumentDetail
from app.services.workflow_service import WorkflowService

router = APIRouter(prefix="/workflow", tags=["Workflow"])


def service() -> WorkflowService:
    return WorkflowService(get_frappe_client())


@router.get("/pending-approvals", response_model=ApiResponse[PendingApprovalsResponse])
async def pending_approvals(request: Request, user: CurrentUserDep, doctype: str | None = Query(None), limit: int = Query(50, ge=1, le=200)) -> ApiResponse[PendingApprovalsResponse]:
    return ApiResponse(data=await service().list_pending_approvals(doctype, get_frappe_cookies(request), limit, user.user))


@router.get("/documents/{doctype}/{name}", response_model=ApiResponse[WorkflowDocumentDetail])
async def document_detail(doctype: str, name: str, request: Request, user: CurrentUserDep) -> ApiResponse[WorkflowDocumentDetail]:
    return ApiResponse(data=await service().get_document_detail(doctype, name, get_frappe_cookies(request), user.user))


@router.get("/documents/{doctype}/{name}/actions", response_model=ApiResponse[list[WorkflowAction]])
async def document_actions(doctype: str, name: str, request: Request, user: CurrentUserDep) -> ApiResponse[list[WorkflowAction]]:
    return ApiResponse(data=await service().get_available_actions(doctype, name, get_frappe_cookies(request), user.user))


@router.post("/apply-action", response_model=ApiResponse[ApplyWorkflowActionResponse])
async def apply_action(payload: ApplyWorkflowActionRequest, request: Request, user: CurrentUserDep) -> ApiResponse[ApplyWorkflowActionResponse]:
    return ApiResponse(data=await service().apply_action(payload, get_frappe_cookies(request), user.user))
