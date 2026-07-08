import pytest

from app.schemas.chat import ChatMessageRequest
from app.services.chat_service import ChatService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "prompt",
    [
        "show monthly sales trend for 2025",
        "show top 10 customers by outstanding",
        "show purchase orders by supplier as bar chart",
        "show sales orders by status as pie chart",
    ],
)
async def test_chat_returns_table_and_chart_for_aggregation(prompt):
    response = await ChatService().send_chat_message(ChatMessageRequest(message=prompt))

    assert response.intent == "aggregation"
    assert any(part.type == "table" for part in response.parts)
    assert any(part.type == "chart" for part in response.parts)
    assert any(action.action_type == "pin_to_overview" for action in response.suggested_actions)


@pytest.mark.asyncio
async def test_empty_source_rows_returns_without_crash(monkeypatch):
    from app.services import erpnext_service

    original = erpnext_service.ERPNextService._mock_records
    monkeypatch.setattr(erpnext_service.ERPNextService, "_mock_records", staticmethod(lambda doctype, filters: []))
    response = await ChatService().send_chat_message(ChatMessageRequest(message="show top 10 customers by outstanding"))
    monkeypatch.setattr(erpnext_service.ERPNextService, "_mock_records", original)

    assert response.intent == "aggregation"
    assert "No matching data" in response.content
