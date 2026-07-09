from fastapi import APIRouter, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.modules import ModuleDashboardResponse, ModuleDetail, ModuleRecords, ModuleReports, ModuleSummary
from app.services.module_service import module_service

router = APIRouter(prefix="/modules", tags=["Modules"])


@router.get("", response_model=ApiResponse[list[ModuleSummary]])
async def modules(request: Request, _: CurrentUserDep) -> ApiResponse[list[ModuleSummary]]:
    return ApiResponse(data=await module_service.list_modules(get_frappe_cookies(request)))


@router.get("/{module_name}", response_model=ApiResponse[ModuleDetail])
async def module(module_name: str, request: Request, _: CurrentUserDep) -> ApiResponse[ModuleDetail]:
    return ApiResponse(data=await module_service.get_module(module_name, get_frappe_cookies(request)))


@router.get("/{module_name}/dashboard", response_model=ApiResponse[ModuleDashboardResponse])
async def module_dashboard(module_name: str, request: Request, _: CurrentUserDep) -> ApiResponse[ModuleDashboardResponse]:
    return ApiResponse(data=await module_service.get_module_dashboard(module_name, get_frappe_cookies(request)))


@router.get("/{module_name}/records", response_model=ApiResponse[ModuleRecords])
async def records(module_name: str, request: Request, _: CurrentUserDep) -> ApiResponse[ModuleRecords]:
    return ApiResponse(data=await module_service.records(module_name, get_frappe_cookies(request)))


@router.get("/{module_name}/reports", response_model=ApiResponse[ModuleReports])
async def reports(module_name: str, request: Request, _: CurrentUserDep) -> ApiResponse[ModuleReports]:
    return ApiResponse(data=await module_service.reports(module_name, get_frappe_cookies(request)))
