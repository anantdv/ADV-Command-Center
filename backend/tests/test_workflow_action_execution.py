from fastapi.testclient import TestClient

from app.main import app


def test_apply_workflow_action_uses_workflow_endpoint_contract():
    client = TestClient(app)
    response = client.post("/api/workflow/apply-action", json={"doctype": "Sales Invoice", "name": "ACC-SINV-2025-00001", "action": "Approve", "comment": "Approved from test"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["action"] == "Approve"
    assert data["previousState"] == "Pending Approval"
    assert data["newState"] == "Approved"


def test_unavailable_workflow_action_is_blocked():
    client = TestClient(app)
    response = client.post("/api/workflow/apply-action", json={"doctype": "Sales Invoice", "name": "ACC-SINV-2025-00001", "action": "Submit"})

    assert response.status_code in {400, 403}
    assert response.json()["success"] is False


def test_chat_approve_returns_confirmation_not_direct_apply():
    client = TestClient(app)
    response = client.post("/api/chat/message", json={"message": "approve sales invoice ACC-SINV-2025-00001"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["intent"] == "workflow_apply_action"
    assert any(part["type"] == "confirmation" for part in data["parts"])
