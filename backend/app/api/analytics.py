from __future__ import annotations

from fastapi import APIRouter, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.analytics import AnalyticsPlanRequest, AnalyticsPlanResponse, AnalyticsResult, AnalyticsRunRequest
from app.schemas.common import ApiResponse
from app.services.analytics_service import analytics_service

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/catalog", response_model=ApiResponse[dict])
async def catalog(user: CurrentUserDep) -> ApiResponse[dict]:
    return ApiResponse(data=await analytics_service.catalog(user.user))


@router.post("/plan", response_model=ApiResponse[AnalyticsPlanResponse])
async def plan(payload: AnalyticsPlanRequest, user: CurrentUserDep) -> ApiResponse[AnalyticsPlanResponse]:
    return ApiResponse(data=await analytics_service.plan(payload.message, user.user))


@router.post("/run", response_model=ApiResponse[AnalyticsResult])
async def run(payload: AnalyticsRunRequest, request: Request, user: CurrentUserDep) -> ApiResponse[AnalyticsResult]:
    return ApiResponse(data=await analytics_service.run_analytics(payload.analytics_key, payload.filters, payload.date_range, payload.chart_type, payload.limit, get_frappe_cookies(request), user.user))
