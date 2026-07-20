def _send(client, message: str, conversation_id: str | None = None):
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _part(data: dict, kind: str) -> dict:
    return next(part for part in data["parts"] if part["type"] == kind)


def test_purchase_invoice_draft_starts_missing_field_collection(client):
    data = _send(client, "create purchase invoice draft")

    assert data["intent"] == "crud_create"
    assert data["intent"] != "blocked_write"
    missing = _part(data, "missing_fields")
    assert missing["doctype"] == "Purchase Invoice"
    assert {"supplier", "items"}.issubset({field["fieldname"] for field in missing["fields"]})


def test_purchase_invoice_draft_collects_supplier_and_items_in_followup(client):
    initial = _send(client, "create purchase invoice draft")
    conversation_id = initial["conversation_id"]

    followup = _send(
        client,
        "Supplier: ABC Traders\nItems:\nSugar 20 rate 12\nRice 50 rate 8\nWarehouse Main",
        conversation_id,
    )

    assert followup["intent"] == "crud_create"
    preview = _part(followup, "record_preview")
    assert preview["doctype"] == "Purchase Invoice"
    assert preview["after_data"]["supplier"] == "ABC Traders"
    assert len(preview["after_data"]["items"]) == 2
    assert _part(followup, "confirmation")["confirm_label"] == "Create Draft"


def test_payment_and_journal_entries_start_draft_plans_not_blocked(client):
    for prompt, doctype in (
        ("create payment entry draft", "Payment Entry"),
        ("create journal entry draft", "Journal Entry"),
    ):
        data = _send(client, prompt)
        assert data["intent"] == "crud_create"
        assert _part(data, "missing_fields")["doctype"] == doctype
