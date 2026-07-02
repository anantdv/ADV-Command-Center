"""Opt-in integration checks against a real Frappe test site."""

import os

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app

RUN_REAL = os.getenv("RUN_REAL_FRAPPE_TESTS", "false").lower() == "true"
BASE_URL = os.getenv("FRAPPE_BASE_URL")
AUTH_MODE = os.getenv("FRAPPE_AUTH_MODE", "token").lower()
TOKEN_READY = bool(os.getenv("FRAPPE_API_KEY") and os.getenv("FRAPPE_API_SECRET"))
SESSION_ID = os.getenv("FRAPPE_SESSION_ID")
READY = RUN_REAL and bool(BASE_URL) and (TOKEN_READY if AUTH_MODE == "token" else bool(SESSION_ID))

pytestmark = pytest.mark.skipif(
    not READY,
    reason="Set RUN_REAL_FRAPPE_TESTS and real Frappe authentication variables.",
)


@pytest.fixture
def real_client():
    original = {
        "use_mock_data": settings.use_mock_data,
        "frappe_base_url": settings.frappe_base_url,
        "frappe_auth_mode": settings.frappe_auth_mode,
        "frappe_api_key": settings.frappe_api_key,
        "frappe_api_secret": settings.frappe_api_secret,
    }
    settings.use_mock_data = False
    settings.frappe_base_url = BASE_URL or settings.frappe_base_url
    settings.frappe_auth_mode = AUTH_MODE
    settings.frappe_api_key = os.getenv("FRAPPE_API_KEY")
    settings.frappe_api_secret = os.getenv("FRAPPE_API_SECRET")
    with TestClient(app) as client:
        if AUTH_MODE == "session" and SESSION_ID:
            client.cookies.set(settings.frappe_session_cookie_name, SESSION_ID)
        yield client
    for key, value in original.items():
        setattr(settings, key, value)


def assert_success(response):
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True, body
    return body["data"]


def test_real_current_user_context(real_client):
    data = assert_success(real_client.get("/api/erpnext/current-user-context"))
    assert data["user"] and data["roles"]


def test_real_allowed_doctypes(real_client):
    data = assert_success(real_client.get("/api/erpnext/allowed-doctypes"))
    assert isinstance(data, list)


def test_real_customer_schema(real_client):
    data = assert_success(real_client.post("/api/erpnext/doctype-schema", json={"doctype": "Customer"}))
    assert data["doctype"] == "Customer"


def test_real_list_and_optional_get_customer(real_client):
    listed = assert_success(real_client.post("/api/erpnext/list-records", json={"doctype": "Customer", "fields": ["name", "customer_name"], "limit": 10}))
    assert isinstance(listed["records"], list)
    if not listed["records"]:
        pytest.skip("No permitted Customer record is available for get-record testing.")
    name = listed["records"][0]["name"]
    record = assert_success(real_client.post("/api/erpnext/get-record", json={"doctype": "Customer", "name": name, "fields": ["name", "customer_name"]}))
    assert record["record"]["name"] == name


def test_real_read_only_chat(real_client):
    data = assert_success(real_client.post("/api/chat/message", json={"message": "show customers"}))
    assert data["intent"] == "list_records"
    assert data["source"]["source_name"] == "Customer"
    assert any(part["type"] == "tool_call" for part in data["parts"])
