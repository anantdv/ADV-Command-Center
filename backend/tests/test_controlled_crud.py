from app.utils.confirmation_store import confirmation_store


def send(client, message: str):
    response = client.post("/api/chat/message", json={"message": message})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def find_part(data, kind: str):
    return next(part for part in data["parts"] if part["type"] == kind)


def test_create_customer_missing_fields(client):
    data = send(client, "create customer ABC Trading")
    missing = find_part(data, "missing_fields")
    assert data["intent"] == "crud_create"
    assert {field["fieldname"] for field in missing["fields"]} == {"customer_group", "territory"}


def test_create_customer_preview_confirm_and_single_use(client):
    data = send(client, "create customer ABC Trading with customer group Commercial and territory India")
    preview = find_part(data, "record_preview")
    confirmation = find_part(data, "confirmation")
    assert preview["after_data"]["customer_name"] == "ABC Trading"
    assert preview["after_data"]["territory"] == "India"
    assert confirmation["risk_level"] == "medium"

    response = client.post("/api/chat/actions/confirm", json={"confirmation_id": confirmation["confirmation_id"]})
    assert response.status_code == 200, response.text
    result = response.json()["data"]
    assert result["operation"] == "create"
    assert result["doctype"] == "Customer"

    reused = client.post("/api/chat/actions/confirm", json={"confirmation_id": confirmation["confirmation_id"]})
    assert reused.status_code == 410


def test_cancel_confirmation(client):
    data = send(client, "create customer Cancel Me with customer group Commercial and territory India")
    confirmation_id = find_part(data, "confirmation")["confirmation_id"]
    cancelled = client.post("/api/chat/actions/cancel", json={"confirmation_id": confirmation_id})
    assert cancelled.status_code == 200
    assert cancelled.json()["data"]["cancelled"] is True
    assert client.post("/api/chat/actions/confirm", json={"confirmation_id": confirmation_id}).status_code == 410


def test_continue_missing_fields_to_preview(client):
    initial = send(client, "create customer Continue Me")
    missing = find_part(initial, "missing_fields")
    response = client.post("/api/chat/actions/continue-crud", json={
        "operation": "create",
        "doctype": "Customer",
        "data": {**missing["collected_data"], "customer_group": "Commercial", "territory": "India"},
        "conversation_id": missing["conversation_id"],
        "message_id": missing["message_id"],
    })
    assert response.status_code == 200, response.text
    assert find_part(response.json()["data"], "confirmation")


def test_update_customer_preview_and_confirm(client):
    data = send(client, "update customer ABC Trading territory to India")
    preview = find_part(data, "record_preview")
    assert preview["before_data"]["territory"] == "Fiji"
    assert preview["after_data"]["territory"] == "India"
    confirmation_id = find_part(data, "confirmation")["confirmation_id"]
    result = client.post("/api/chat/actions/confirm", json={"confirmation_id": confirmation_id})
    assert result.status_code == 200, result.text
    assert result.json()["data"]["operation"] == "update"


def test_unsupported_and_high_risk_writes_are_blocked(client):
    for prompt in (
        "create sales invoice for ABC",
        "delete customer ABC Trading",
        "submit invoice ACC-SINV-2026-00001",
        "create payment entry for customer ABC",
        "create journal entry",
        "bulk update all customers",
    ):
        data = send(client, prompt)
        assert data["intent"] == "blocked_write"
        assert data["permission"]["allowed"] is False


def test_support_ticket_description_can_mention_blocked_erp_action(client):
    data = send(client, "create support ticket user cannot submit invoice")
    preview = find_part(data, "record_preview")
    assert data["intent"] == "crud_create"
    assert preview["doctype"] == "Issue"
    assert preview["after_data"]["subject"] == "user cannot submit invoice"


def test_blocked_field_is_rejected(client):
    response = client.post("/api/chat/message", json={"message": "update customer ABC Trading docstatus to 1"})
    assert response.status_code == 422
    assert "not allowed" in response.json()["message"]


def test_expired_confirmation_is_rejected(client):
    confirmation_id = confirmation_store.create({"operation":"create","doctype":"Customer","record_name":None,"data":{"customer_name":"Expired"},"user":"admin@example.com","conversation_id":None}, expires_in_seconds=-1)
    response = client.post("/api/chat/actions/confirm", json={"confirmation_id": confirmation_id})
    assert response.status_code == 410
