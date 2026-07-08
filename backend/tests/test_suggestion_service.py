import pytest

from app.schemas.suggestions import SuggestionContext
from app.services.suggestion_service import SuggestionService


@pytest.mark.asyncio
async def test_suggestion_service_limits_results():
    ctx = SuggestionContext(result_type="table", doctype="Sales Invoice", source_name="Sales Invoice", row_count=20, message_id="msg_1", conversation_id="conv_1", filters={"status": "Overdue"})
    result = await SuggestionService().generate_suggestions(ctx, [], user="tester")
    assert 0 < len(result.suggestions) <= 6
    assert "Group by Customer" in [item.label for item in result.suggestions]


def test_chat_response_includes_contextual_suggestions(client):
    response = client.post("/api/chat/message", json={"message": "show unpaid invoices for May 2025"})
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["suggestions"]
    labels = [item["label"] for item in data["suggestions"]]
    assert "Group by Customer" in labels
    assert "Export to Excel" in labels


def test_suggestions_generate_endpoint(client):
    response = client.post("/api/suggestions/generate", json={"resultType": "table", "doctype": "Item", "sourceName": "Item", "rowCount": 2, "messageId": "msg_1"})
    assert response.status_code == 200, response.text
    labels = [item["label"] for item in response.json()["data"]["suggestions"]]
    assert "Show Stock Balance" in labels
