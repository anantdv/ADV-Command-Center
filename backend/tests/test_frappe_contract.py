from typing import Any

import pytest

from app.config import settings
from app.services.erpnext_service import ERPNextService


class FakeFrappeClient:
    def __init__(self, responses: dict[str, dict[str, Any]]):
        self.responses = responses
        self.last_json: dict[str, Any] | None = None

    async def get(self, path: str, params: dict | None = None, cookies: dict | None = None) -> dict:
        del params, cookies
        return self.responses[path]

    async def post(self, path: str, json: dict | None = None, cookies: dict | None = None) -> dict:
        del cookies
        self.last_json = json
        return self.responses[path]


@pytest.fixture
def real_service_mode():
    original = settings.use_mock_data
    settings.use_mock_data = False
    yield
    settings.use_mock_data = original


@pytest.mark.asyncio
async def test_companion_list_response_is_adapted(real_service_mode):
    client = FakeFrappeClient({
        "/api/method/ai_command_center.api.crud.list_records": {
            "message": {
                "success": True,
                "data": {
                    "records": [{"name": "CUST-0001", "customer_name": "ABC"}],
                    "count": 1,
                    "permission": {
                        "allowed": True,
                        "risk_level": "low",
                        "confirmation_required": False,
                        "filtered_fields": ["name", "customer_name"],
                        "blocked_fields": [],
                    },
                },
            }
        }
    })
    result = await ERPNextService(client).list_records(
        "Customer",
        fields=["name", "customer_name"],
    )
    assert result.total == 1
    assert result.records[0]["customer_name"] == "ABC"
    assert result.permissions.allowed is True
    assert result.permissions.filtered_fields == ["name", "customer_name"]


@pytest.mark.asyncio
async def test_companion_schema_reqd_is_mapped(real_service_mode):
    client = FakeFrappeClient({
        "/api/method/ai_command_center.api.schema.get_doctype_schema": {
            "message": {
                "success": True,
                "data": {
                    "doctype": "Customer",
                    "module": "Selling",
                    "fields": [{"fieldname": "customer_name", "label": "Customer Name", "fieldtype": "Data", "reqd": 1}],
                    "permissions": {"can_read": True, "can_create": True},
                },
            }
        }
    })
    result = await ERPNextService(client).get_doctype_schema("Customer")
    assert result.fields[0].required is True
    assert result.permissions.can_create is True


@pytest.mark.asyncio
async def test_create_record_sends_companion_contract(real_service_mode):
    client = FakeFrappeClient({
        "/api/method/ai_command_center.api.crud.create_record": {
            "message": {
                "success": True,
                "data": {
                    "name": "CUST-0002",
                    "docstatus": 0,
                    "status": "Draft",
                    "permission": {"allowed": True, "risk_level": "medium"},
                },
            }
        }
    })
    result = await ERPNextService(client).create_record("Customer", {"customer_name": "ABC"})
    assert client.last_json == {"doctype": "Customer", "data": {"customer_name": "ABC"}}
    assert result.record["name"] == "CUST-0002"
    assert result.permissions.risk_level == "medium"
