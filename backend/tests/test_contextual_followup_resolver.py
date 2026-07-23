def _send(client, message: str, conversation_id: str | None = None, structured_action: dict | None = None):
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    if structured_action:
        payload["structured_action"] = structured_action
        payload["source"] = "generated_action"
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200, response.text
    return response.json()["data"]


def _part(data: dict, kind: str) -> dict:
    return next(part for part in data["parts"] if part["type"] == kind)


def test_short_warehouse_reply_updates_warehouse_not_item_query(client):
    first = _send(client, "create a draft purchase order for supplier Zucci for items ITEM-001 qty1")
    conversation_id = first["conversation_id"]
    resolution = _part(first, "child_rows_resolution_required")
    supplier_row = next(row for row in resolution["rows"] if row["link_field"] == "supplier")

    after_supplier = _send(
        client,
        "Selected 001463",
        conversation_id,
        {
            "action": "select_entity_match",
            "draft_session_id": conversation_id,
            "table_field": "__parent__",
            "row_id": supplier_row["row_id"],
            "fieldname": "supplier",
            "selected_value": "001463",
        },
    )
    assert after_supplier["intent"] == "draft_field_options"
    assert after_supplier["current_state"] == "DRAFT_INFORMATION_REQUIRED"
    assert after_supplier["next_expected_action"] == "user_input"

    preview_response = _send(client, "use pom warehouse", conversation_id)
    preview = _part(preview_response, "record_preview")
    rows = preview["after_data"]["items"]

    assert preview_response["intent"] == "crud_create"
    assert preview_response["response_type"] == "draft_preview"
    assert rows[0]["item_code"] == "ITEM-001"
    assert rows[0]["warehouse"] == "POM Warehouse - CTS"
    assert rows[0].get("item_query") not in {"use pom", "use pom warehouse"}


def test_warehouse_option_number_resumes_active_draft(client):
    first = _send(client, "create a draft purchase order for supplier Zucci for items ITEM-001 qty1")
    conversation_id = first["conversation_id"]
    resolution = _part(first, "child_rows_resolution_required")
    supplier_row = next(row for row in resolution["rows"] if row["link_field"] == "supplier")

    _send(
        client,
        "Selected 001463",
        conversation_id,
        {
            "action": "select_entity_match",
            "draft_session_id": conversation_id,
            "table_field": "__parent__",
            "row_id": supplier_row["row_id"],
            "fieldname": "supplier",
            "selected_value": "001463",
        },
    )

    preview_response = _send(client, "1", conversation_id)
    preview = _part(preview_response, "record_preview")

    assert preview_response["intent"] == "crud_create"
    assert preview["after_data"]["set_warehouse"] == "Stores - CTS"
