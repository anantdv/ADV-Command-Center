from __future__ import annotations

from fastapi import APIRouter, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.metadata import DocumentInspectionResponse, DoctypeIntelligence, FormLayoutIntelligence
from app.services.document_inspector import document_inspector
from app.services.metadata_service import metadata_service

router = APIRouter(prefix="/metadata", tags=["ERP Metadata"])


@router.get("/doctypes/{doctype}/intelligence", response_model=ApiResponse[DoctypeIntelligence])
async def doctype_intelligence(doctype: str, request: Request, _: CurrentUserDep, refresh: bool = False) -> ApiResponse[DoctypeIntelligence]:
    return ApiResponse(data=await metadata_service.get_doctype_intelligence(doctype, get_frappe_cookies(request), refresh))


@router.get("/doctypes/{doctype}/form", response_model=ApiResponse[FormLayoutIntelligence])
async def doctype_form(doctype: str, request: Request, _: CurrentUserDep) -> ApiResponse[FormLayoutIntelligence]:
    return ApiResponse(data=await metadata_service.get_form_layout(doctype, get_frappe_cookies(request)))


@router.get("/doctypes/{doctype}/inspect", response_model=ApiResponse[DocumentInspectionResponse])
async def inspect_doctype(doctype: str, request: Request, _: CurrentUserDep) -> ApiResponse[DocumentInspectionResponse]:
    return ApiResponse(data=await document_inspector.inspect(doctype, cookies=get_frappe_cookies(request)))


@router.get("/doctypes/{doctype}/documents/{name}/inspect", response_model=ApiResponse[DocumentInspectionResponse])
async def inspect_document(doctype: str, name: str, request: Request, _: CurrentUserDep) -> ApiResponse[DocumentInspectionResponse]:
    return ApiResponse(data=await document_inspector.inspect(doctype, name=name, cookies=get_frappe_cookies(request)))

