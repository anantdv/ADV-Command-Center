from __future__ import annotations

from fastapi import APIRouter, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.report_composer import (
    ReportComposerDebugResponse,
    ReportComposerPlan,
    ReportComposerPlanRequest,
    ReportComposerResult,
    ReportComposerRunRequest,
    SaveReportViewRequest,
    SavedReportView,
)
from app.schemas.file_generation import GenerateFileRequest, GenerateFileResponse
from app.schemas.dashboard import DashboardWidgetCreateRequest, DashboardWidgetData, DashboardWidgetSource
from app.services.dashboard_service import dashboard_service
from app.services.file_generation_service import file_generation_service
from app.services.report_composer_service import report_composer_service
from app.utils.report_filter_builder import build_normalized_filters_from_plan

router = APIRouter(prefix="/report-composer", tags=["Report Composer"])


@router.get("/sources", response_model=ApiResponse[dict])
async def sources() -> ApiResponse[dict]:
    return ApiResponse(data=await report_composer_service.sources())


@router.get("/sources/{source_name}/fields", response_model=ApiResponse[dict])
async def fields(source_name: str) -> ApiResponse[dict]:
    return ApiResponse(data=await report_composer_service.fields(source_name))


@router.post("/plan", response_model=ApiResponse[ReportComposerPlan])
async def plan(payload: ReportComposerPlanRequest, request: Request) -> ApiResponse[ReportComposerPlan]:
    return ApiResponse(data=await report_composer_service.plan_report(payload, get_frappe_cookies(request)))


@router.post("/run", response_model=ApiResponse[ReportComposerResult])
async def run(payload: ReportComposerRunRequest, request: Request, user: CurrentUserDep) -> ApiResponse[ReportComposerResult]:
    return ApiResponse(data=await report_composer_service.run_report(payload, get_frappe_cookies(request), user.user))


@router.post("/views", response_model=ApiResponse[SavedReportView])
async def save_view(payload: SaveReportViewRequest, user: CurrentUserDep) -> ApiResponse[SavedReportView]:
    return ApiResponse(data=await report_composer_service.save_view(payload, user.user, user.roles))


@router.get("/views", response_model=ApiResponse[list[SavedReportView]])
async def list_views(user: CurrentUserDep) -> ApiResponse[list[SavedReportView]]:
    return ApiResponse(data=await report_composer_service.list_views(user.user, user.roles))


@router.get("/views/{view_id}", response_model=ApiResponse[SavedReportView])
async def get_view(view_id: str, user: CurrentUserDep) -> ApiResponse[SavedReportView]:
    return ApiResponse(data=await report_composer_service.get_view(view_id, user.user, user.roles))


@router.delete("/views/{view_id}", response_model=ApiResponse[bool])
async def delete_view(view_id: str, user: CurrentUserDep) -> ApiResponse[bool]:
    return ApiResponse(data=await report_composer_service.delete_view(view_id, user.user, user.roles))


@router.post("/views/{view_id}/run", response_model=ApiResponse[ReportComposerResult])
async def run_view(view_id: str, request: Request, user: CurrentUserDep) -> ApiResponse[ReportComposerResult]:
    view = await report_composer_service.get_view(view_id, user.user, user.roles)
    return ApiResponse(data=await report_composer_service.run_report(ReportComposerRunRequest(plan=view.plan), get_frappe_cookies(request), user.user))


@router.post("/export", response_model=ApiResponse[GenerateFileResponse])
async def export(payload: ReportComposerRunRequest, request: Request, user: CurrentUserDep, file_format: str = "xlsx") -> ApiResponse[GenerateFileResponse]:
    result = await report_composer_service.run_report(payload, get_frappe_cookies(request), user.user)
    fmt = file_format if file_format in {"xlsx", "csv", "pdf", "html", "png"} else "xlsx"
    generated = await file_generation_service.generate_file(GenerateFileRequest(
        source_type="chat_result",
        source_name=result.plan.title or result.plan.source.source_name,
        file_format=fmt,  # type: ignore[arg-type]
        title=result.plan.title,
        filters=result.filters_applied,
        rows=result.rows,
        chart_config=result.chart,
    ), get_frappe_cookies(request), user.user)
    return ApiResponse(data=generated)


@router.post("/pin-to-dashboard", response_model=ApiResponse[DashboardWidgetData])
async def pin_to_dashboard(payload: ReportComposerRunRequest, request: Request, user: CurrentUserDep) -> ApiResponse[DashboardWidgetData]:
    plan = payload.plan
    source = DashboardWidgetSource(
        source_type="manual_config",
        source_name=plan.title or plan.source.source_name,
        doctype=plan.source.source_name,
        filters={"report_composer_plan": plan.model_dump(mode="json")},
    )
    widget = await dashboard_service.create_widget(DashboardWidgetCreateRequest(
        title=plan.title or "Custom Report",
        widget_type="bar_chart" if plan.chart.chart_type in {"bar", "none"} else f"{plan.chart.chart_type}_chart",  # type: ignore[arg-type]
        source=source,
        chart_config={"report_composer": True, "chart_type": plan.chart.chart_type},
    ), get_frappe_cookies(request), user.user)
    return ApiResponse(data=widget, message="Pinned to Overview successfully.")


@router.post("/debug-plan", response_model=ApiResponse[ReportComposerDebugResponse])
async def debug_plan(payload: ReportComposerPlanRequest, request: Request) -> ApiResponse[ReportComposerDebugResponse]:
    plan = await report_composer_service.plan_report(payload, get_frappe_cookies(request))
    return ApiResponse(data=ReportComposerDebugResponse(
        plan=plan,
        validated_plan=plan,
        normalized_filters=build_normalized_filters_from_plan(plan),
        required_source_fields=report_composer_service._required_source_fields(plan),
        warnings=plan.warnings,
    ))
