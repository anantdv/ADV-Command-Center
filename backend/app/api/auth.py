from fastapi import APIRouter, Request, Response

from app.config import settings
from app.dependencies import CurrentUserDep
from app.schemas.auth import CurrentUser, LoginRequest, LoginResult
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])
service = AuthService()


@router.get("/me", response_model=ApiResponse[CurrentUser])
async def me(user: CurrentUserDep) -> ApiResponse[CurrentUser]:
    return ApiResponse(data=await service.me(user))


@router.post("/login", response_model=ApiResponse[LoginResult])
async def login(payload: LoginRequest, response: Response) -> ApiResponse[LoginResult]:
    session = await service.login(payload)
    response.set_cookie(
        key=settings.frappe_session_cookie_name,
        value=session.session_id,
        httponly=True,
        secure=settings.app_env.lower() == "production",
        samesite="lax",
        max_age=3 * 24 * 60 * 60,
        path="/",
    )
    return ApiResponse(data=session.result)


@router.post("/logout", response_model=ApiResponse[dict])
async def logout(request: Request, response: Response) -> ApiResponse[dict]:
    cookie_name = settings.frappe_session_cookie_name
    await service.logout(request.cookies.get(cookie_name))
    response.delete_cookie(cookie_name, path="/")
    return ApiResponse(data={"loggedOut": True})
