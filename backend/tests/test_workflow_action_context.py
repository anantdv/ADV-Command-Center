from fastapi.testclient import TestClient

from app.main import app


def _send(client: TestClient, message: str, conversation_id: str | None = None):
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _send_action(client: TestClient, message: str, conversation_id: str, action: dict):
    payload = {"message": message, "conversation_id": conversation_id, "source": "generated_action", "structured_action": action}
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_approve_it_resolves_to_open_workflow_document():
    client = TestClient(app)
    detail = _send(client, "show detail for Sales Invoice ACC-SINV-2025-00001")
    approval = _send(client, "approve it", detail["conversation_id"])

    assert approval["intent"] == "workflow_apply_action"
    part = next(part for part in approval["parts"] if part["type"] == "workflow_confirmation")
    assert part["doctype"] == "Sales Invoice"
    assert part["name"] == "ACC-SINV-2025-00001"
    assert part["action"] == "Approve"


def test_approve_it_without_context_returns_workflow_clarification_not_safety_guard():
    client = TestClient(app)
    response = _send(client, "approve it")

    assert response["intent"] == "workflow_apply_action"
    assert response["permission"]["allowed"] is False
    assert "open workflow document" in response["content"].lower()
    assert "safety" not in response["content"].lower()


def test_direct_submit_remains_blocked():
    client = TestClient(app)
    response = _send(client, "submit purchase order PUR-ORD-2025-00007")

    assert response["intent"] == "blocked_write"
    assert response["permission"]["allowed"] is False


def test_structured_open_document_detail_bypasses_stale_draft_context():
    client = TestClient(app)
    draft = _send(client, "create po for bnbm")
    detail = _send_action(
        client,
        "Open Purchase Order PUR-ORD-2025-00007",
        draft["conversation_id"],
        {"action": "open_document_detail", "doctype": "Purchase Order", "name": "PUR-ORD-2025-00007"},
    )

    assert detail["intent"] == "workflow_get_detail"
    assert detail["response_type"] == "workflow_detail"
    assert "item" not in detail["content"].lower()


def test_structured_refresh_pending_approvals_bypasses_stale_draft_context():
    client = TestClient(app)
    draft = _send(client, "create po for bnbm")
    refreshed = _send_action(
        client,
        "Refresh",
        draft["conversation_id"],
        {"action": "refresh_result", "result_type": "pending_approvals"},
    )

    assert refreshed["intent"] == "workflow_list_pending"
    assert refreshed["response_type"] == "workflow_list_pending"
    assert "refresh" not in refreshed["content"].lower() or "pending" in refreshed["content"].lower()
