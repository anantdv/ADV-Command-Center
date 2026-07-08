from fastapi.testclient import TestClient

from app.main import app


def test_pending_approvals_list_returns_mock_documents():
    client = TestClient(app)
    response = client.get("/api/workflow/pending-approvals")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] >= 1
    assert data["documents"][0]["availableActions"]


def test_pending_approvals_can_filter_doctype():
    client = TestClient(app)
    response = client.get("/api/workflow/pending-approvals?doctype=Sales%20Invoice")

    assert response.status_code == 200
    docs = response.json()["data"]["documents"]
    assert docs
    assert all(doc["doctype"] == "Sales Invoice" for doc in docs)


def test_document_detail_includes_available_actions():
    client = TestClient(app)
    response = client.get("/api/workflow/documents/Sales%20Invoice/ACC-SINV-2025-00001")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["doctype"] == "Sales Invoice"
    assert {action["action"] for action in data["availableActions"]} >= {"Approve", "Reject"}


def test_chat_pending_approvals():
    client = TestClient(app)
    response = client.post("/api/chat/message", json={"message": "show my pending approvals"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["intent"] == "workflow_list_pending"
    assert any(part["type"] == "table" for part in data["parts"])
