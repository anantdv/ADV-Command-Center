import httpx
import pytest

from app.config import settings
from app.core.exceptions import AuthenticationError
from app.schemas.auth import LoginRequest
from app.services.auth_service import AuthService


@pytest.fixture
def real_auth_mode():
    original = settings.use_mock_data
    settings.use_mock_data = False
    yield
    settings.use_mock_data = original


@pytest.mark.asyncio
async def test_invalid_frappe_credentials_are_rejected(real_auth_mode):
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/method/login"
        return httpx.Response(401, json={"message": "Invalid login credentials"})

    service = AuthService(httpx.MockTransport(handler))
    with pytest.raises(AuthenticationError, match="Invalid ERPNext"):
        await service.login(LoginRequest(username="invalid@example.com", password="wrong"))


@pytest.mark.asyncio
async def test_valid_frappe_login_requires_and_returns_sid(real_auth_mode):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"message": "Logged In", "full_name": "Test User"},
            headers={"set-cookie": "sid=test-session-id; HttpOnly; Path=/; SameSite=Lax"},
        )

    service = AuthService(httpx.MockTransport(handler))
    session = await service.login(LoginRequest(username="test@example.com", password="valid"))
    assert session.session_id == "test-session-id"
    assert session.result.full_name == "Test User"
