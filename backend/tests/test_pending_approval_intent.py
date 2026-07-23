from app.utils.workflow_intent_parser import parse_workflow_intent


def _send(client, message: str):
    response = client.post("/api/chat/message", json={"message": message})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_pending_approval_parser_handles_singular():
    intent = parse_workflow_intent("show me my pending approval")
    assert intent
    assert intent["intent"] == "workflow_list_pending"


def test_pending_approval_parser_handles_plural():
    intent = parse_workflow_intent("show my pending approvals")
    assert intent
    assert intent["intent"] == "workflow_list_pending"


def test_pending_approval_parser_handles_document_phrase():
    intent = parse_workflow_intent("show documents pending for my approval")
    assert intent
    assert intent["intent"] == "workflow_list_pending"


def test_pending_approval_parser_handles_doctype_specific_phrase():
    intent = parse_workflow_intent("show pending sales invoice approvals")
    assert intent
    assert intent["intent"] == "workflow_list_pending"
    assert intent["doctype"] == "Sales Invoice"


def test_chat_pending_approvals_does_not_return_generic_fallback(client):
    data = _send(client, "show me my pending approval")
    assert data["intent"] == "workflow_list_pending"
    assert "ERPNext queries such as" not in data["content"]


def test_workflow_action_parser_handles_send_back():
    intent = parse_workflow_intent("send back purchase order PUR-ORD-2026-00025")
    assert intent
    assert intent["intent"] == "workflow_apply_action"
    assert intent["action"] == "Send Back"


def test_contextual_approve_maps_to_custom_available_action():
    context = {
        "active_doctype": "Sales Order",
        "active_document": "SAL-ORD-2026-00001",
        "active_workflow_actions": [{"action": "Approved By Sales Person"}, {"action": "Rejected By Sales Person"}],
    }
    intent = parse_workflow_intent("approve it", context)

    assert intent
    assert intent["doctype"] == "Sales Order"
    assert intent["record_name"] == "SAL-ORD-2026-00001"
    assert intent["action"] == "Approved By Sales Person"
