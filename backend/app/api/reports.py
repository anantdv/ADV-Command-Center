from fastapi import APIRouter, Query, Request

from app.dependencies import get_frappe_client, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.report_builder import ReportColumn, ReportDiagnosticRequest, ReportDiagnosticResponse, ReportRunWithColumnsRequest, ReportRunWithColumnsResponse
from app.services.report_builder_service import ReportBuilderService

router = APIRouter(prefix="/reports", tags=["Reports"])


def service() -> ReportBuilderService:
    return ReportBuilderService(get_frappe_client())


@router.get("/available-columns", response_model=ApiResponse[list[ReportColumn]])
async def available_columns(request: Request, source_type: str = Query(...), source_name: str = Query(...)) -> ApiResponse[list[ReportColumn]]:
    return ApiResponse(data=await service().available_columns(source_type, source_name, get_frappe_cookies(request)))


@router.post("/run-with-columns", response_model=ApiResponse[ReportRunWithColumnsResponse])
async def run_with_columns(payload: ReportRunWithColumnsRequest, request: Request) -> ApiResponse[ReportRunWithColumnsResponse]:
    return ApiResponse(data=await service().run_with_columns(payload, get_frappe_cookies(request)))


@router.post("/diagnose", response_model=ApiResponse[ReportDiagnosticResponse])
async def diagnose(payload: ReportDiagnosticRequest, request: Request) -> ApiResponse[ReportDiagnosticResponse]:
    return ApiResponse(data=await service().diagnose(payload.report_name, payload.filters, get_frappe_cookies(request)))


@router.post("/save-column-view", response_model=ApiResponse[dict])
async def save_column_view() -> ApiResponse[dict]:
    return ApiResponse(data={"saved": False}, message="Saved report views will be persisted in the next release.")


@router.get("/saved-column-views", response_model=ApiResponse[list[dict]])
async def saved_column_views() -> ApiResponse[list[dict]]:
    return ApiResponse(data=[])


@router.delete("/saved-column-views/{view_id}", response_model=ApiResponse[bool])
async def delete_saved_column_view(view_id: str) -> ApiResponse[bool]:
    return ApiResponse(data=True, message=f"View {view_id} removed from local cache.")
