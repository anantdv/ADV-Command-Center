from typing import Annotated

from fastapi import Depends, Request

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.core.permissions import PermissionGuard
from app.db.seed import MOCK_USER
from app.frappe.client import FrappeClient
from app.schemas.auth import CurrentUser


def get_frappe_cookies(request: Request) -> dict[str, str]:
    """Forward only the configured Frappe session cookie, never arbitrary cookies."""
    if settings.use_mock_data or settings.frappe_auth_mode != "session":
        return {}
    if not settings.frappe_forward_session_cookie:
        raise AuthenticationError("Frappe session forwarding is disabled.")
    cookie_name = settings.frappe_session_cookie_name
    session_id = request.cookies.get(cookie_name)
    if not session_id:
        raise AuthenticationError(f"Missing Frappe session cookie '{cookie_name}'.")
    return {cookie_name: session_id}


def get_frappe_client() -> FrappeClient:
    return FrappeClient(
        base_url=settings.frappe_base_url,
        auth_mode=settings.frappe_auth_mode,
        api_key=settings.frappe_api_key,
        api_secret=settings.frappe_api_secret,
        session_cookie_name=settings.frappe_session_cookie_name,
    )


async def get_current_app_user(request: Request) -> CurrentUser:
    if settings.use_mock_data:
        return CurrentUser(**MOCK_USER)
    from app.services.erpnext_service import ERPNextService

    context = await ERPNextService(get_frappe_client()).get_current_user_context(
        get_frappe_cookies(request)
    )
    return CurrentUser(
        user=context.user,
        full_name=context.full_name,
        first_name=(context.full_name or context.user).split()[0] if (context.full_name or context.user) else None,
        avatar=None,
        roles=context.roles,
        company=context.company or "",
        company_currency=context.company_currency,
        allowed_companies=context.allowed_companies,
        timezone=context.timezone,
        language=context.language,
    )


async def get_current_user(request: Request) -> CurrentUser:
    """Backward-compatible dependency name used by existing routers."""
    return await get_current_app_user(request)


def get_permission_guard(user: Annotated[CurrentUser, Depends(get_current_app_user)]) -> PermissionGuard:
    return PermissionGuard(user.roles)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_app_user)]
PermissionGuardDep = Annotated[PermissionGuard, Depends(get_permission_guard)]
