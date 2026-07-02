from dataclasses import dataclass
from http.cookies import SimpleCookie

import httpx
import structlog

from app.config import settings
from app.core.exceptions import AuthenticationError, FrappeUnavailableError
from app.db.seed import MOCK_USER
from app.schemas.auth import CurrentUser, LoginRequest, LoginResult

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class FrappeLoginSession:
    result: LoginResult
    session_id: str


class AuthService:
    def __init__(self, transport: httpx.AsyncBaseTransport | None = None):
        self.transport = transport

    async def me(self, user: CurrentUser) -> CurrentUser:
        return user

    async def login(self, request: LoginRequest) -> FrappeLoginSession:
        if settings.use_mock_data:
            return FrappeLoginSession(
                result=LoginResult(
                    user=request.username,
                    full_name=MOCK_USER["full_name"],
                    email=request.username,
                    roles=MOCK_USER["roles"],
                    message="Mock session active",
                ),
                session_id="mock-session",
            )

        try:
            async with httpx.AsyncClient(
                base_url=settings.frappe_base_url.rstrip("/"),
                timeout=httpx.Timeout(30.0, connect=10.0),
                follow_redirects=False,
                transport=self.transport,
                headers={"Accept": "application/json", "Content-Type": "application/json"},
            ) as client:
                response = await client.post(
                    "/api/method/login",
                    json={"usr": request.username.strip(), "pwd": request.password},
                )
        except httpx.RequestError as exc:
            raise FrappeUnavailableError("Unable to reach the Frappe login service.") from exc

        payload = self._json_payload(response)
        if response.status_code >= 400 or payload.get("exc") or payload.get("exception"):
            logger.warning("frappe_login_rejected", status=response.status_code)
            raise AuthenticationError("Invalid ERPNext username or password.")

        session_id = response.cookies.get(settings.frappe_session_cookie_name)
        if not session_id:
            session_id = self._cookie_from_header(
                response.headers.get("set-cookie", ""),
                settings.frappe_session_cookie_name,
            )
        if not session_id:
            raise AuthenticationError("ERPNext did not return a valid authenticated session.")

        user = request.username.strip()
        return FrappeLoginSession(
            result=LoginResult(
                user=user,
                full_name=str(payload.get("full_name") or user),
                email=user if "@" in user else None,
                message=str(payload.get("message") or "Logged in"),
            ),
            session_id=session_id,
        )

    async def logout(self, session_id: str | None) -> None:
        if settings.use_mock_data or not session_id:
            return
        try:
            async with httpx.AsyncClient(
                base_url=settings.frappe_base_url.rstrip("/"),
                timeout=httpx.Timeout(10.0, connect=5.0),
                transport=self.transport,
                headers={"Accept": "application/json"},
            ) as client:
                await client.get(
                    "/api/method/logout",
                    cookies={settings.frappe_session_cookie_name: session_id},
                )
        except httpx.RequestError:
            logger.warning("frappe_logout_unreachable")

    @staticmethod
    def _json_payload(response: httpx.Response) -> dict:
        try:
            payload = response.json()
        except ValueError as exc:
            raise AuthenticationError("ERPNext returned an invalid login response.") from exc
        return payload if isinstance(payload, dict) else {}

    @staticmethod
    def _cookie_from_header(header: str, name: str) -> str | None:
        cookie = SimpleCookie()
        try:
            cookie.load(header)
        except Exception:
            return None
        morsel = cookie.get(name)
        return morsel.value if morsel else None
