from fastapi import APIRouter, Query, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.dashboard import DashboardOverviewResponse, DashboardWidgetCreateRequest, DashboardWidgetData, DashboardWidgetReorderRequest, DashboardWidgetUpdateRequest
from app.utils.chart_builder import normalize_chart_widget_data
from app.services.dashboard_service import dashboard_service

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/overview", response_model=ApiResponse[DashboardOverviewResponse])
async def overview(request: Request, user: CurrentUserDep, from_date: str | None = Query(default=None), to_date: str | None = Query(default=None)): return ApiResponse(data=await dashboard_service.get_overview(get_frappe_cookies(request), user.user, user.roles))


@router.get("/widgets", response_model=ApiResponse[list[DashboardWidgetData]])
async def widgets(request: Request, user: CurrentUserDep): return ApiResponse(data=await dashboard_service.list_widgets(get_frappe_cookies(request), user.user, user.roles))


@router.post("/widgets", response_model=ApiResponse[DashboardWidgetData])
async def create_widget(payload: DashboardWidgetCreateRequest, request: Request, user: CurrentUserDep): return ApiResponse(data=await dashboard_service.create_widget(payload, get_frappe_cookies(request), user.user), message="Widget created")


@router.get("/widgets/{widget_id}", response_model=ApiResponse[DashboardWidgetData])
async def get_widget(widget_id: str, request: Request, user: CurrentUserDep): return ApiResponse(data=await dashboard_service.get_widget(widget_id, get_frappe_cookies(request), user.user, user.roles))


@router.post("/widgets/{widget_id}/refresh", response_model=ApiResponse[DashboardWidgetData])
async def refresh_widget(widget_id: str, request: Request, user: CurrentUserDep): return ApiResponse(data=await dashboard_service.refresh_widget(widget_id, get_frappe_cookies(request), user.user, user.roles))


@router.put("/widgets/{widget_id}", response_model=ApiResponse[DashboardWidgetData])
async def update_widget(widget_id: str, payload: DashboardWidgetUpdateRequest, request: Request, user: CurrentUserDep): return ApiResponse(data=await dashboard_service.update_widget(widget_id, payload, get_frappe_cookies(request), user.user, user.roles))


@router.delete("/widgets/{widget_id}", response_model=ApiResponse[bool])
async def delete_widget(widget_id: str, request: Request, user: CurrentUserDep): return ApiResponse(data=await dashboard_service.delete_widget(widget_id, get_frappe_cookies(request), user.user, user.roles))


@router.post("/widgets/reorder", response_model=ApiResponse[bool])
async def reorder_widgets(payload: DashboardWidgetReorderRequest, request: Request, user: CurrentUserDep): return ApiResponse(data=await dashboard_service.reorder_widgets(payload.layouts, get_frappe_cookies(request), user.user, user.roles))


@router.post("/widgets/debug-chart", response_model=ApiResponse[dict])
async def debug_chart(payload: dict) -> ApiResponse[dict]:
    normalized = normalize_chart_widget_data(payload.get("widget_type") or "bar_chart", payload.get("rows") or [], payload.get("chart_config"))
    return ApiResponse(data={**normalized, "normalized": True, "warnings": []})
