from fastapi import APIRouter, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.common import ApiResponse
from app.schemas.notifications import NotificationTickerItem
from app.services.notification_service import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/ticker", response_model=ApiResponse[list[NotificationTickerItem]])
async def ticker(request: Request, user: CurrentUserDep) -> ApiResponse[list[NotificationTickerItem]]:
    return ApiResponse(data=await notification_service.ticker(get_frappe_cookies(request), user.user))
