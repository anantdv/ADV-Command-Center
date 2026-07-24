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


@pytest.mark.asyncio
async def test_workflow_pending_suggestions_are_dynamic_from_doctype_counts():
    ctx = SuggestionContext(
        result_type="workflow_pending_list",
        row_count=20,
        message_id="msg_workflow",
        extra={"doctype_counts": [
            {"doctype": "HP APPROVAL FORM", "count": 8},
            {"doctype": "Quotation", "count": 5},
            {"doctype": "Purchase Order", "count": 2},
        ]},
    )
    result = await SuggestionService().generate_suggestions(ctx, [], user="tester")
    labels = [item.label for item in result.suggestions]
    assert "HP Approval Forms · 8" in labels
    assert "Quotations · 5" in labels
    assert "Purchase Orders · 2" in labels
    assert "Sales Invoices · 1" not in labels
    assert "Show Sales Invoice Approvals" not in labels
    assert "Show Purchase Order Approvals" not in labels


@pytest.mark.asyncio
async def test_workflow_pending_filter_suggestion_preserves_structured_payload():
    ctx = SuggestionContext(
        result_type="workflow_pending_list",
        row_count=5,
        message_id="msg_workflow",
        extra={"doctype_counts": [{"doctype": "Quotation", "count": 5}]},
    )
    result = await SuggestionService().generate_suggestions(ctx, [], user="tester")
    quotation = next(item for item in result.suggestions if item.payload.get("doctype") == "Quotation")
    assert quotation.action_type == "filter_pending_approvals"
    assert quotation.payload["action"] == "filter_pending_approvals"
    assert quotation.payload["count"] == 5
