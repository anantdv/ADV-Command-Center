from app.services.conversation_state_engine import normalize_business_abbreviations
from app.schemas.chat import ChatMessageRequest
from app.schemas.conversation_state import ConversationContext, ConversationState
from app.services.conversation_state_engine import ConversationStateEngine


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


def _preview_with_two_items(client):
    first = _send(client, "create po for zucci with items home basic oven 45l qty 2, midea split ac qty1")
    conversation_id = first["conversation_id"]
    resolution = _part(first, "child_rows_resolution_required")
    supplier_row = next(row for row in resolution["rows"] if row["link_field"] == "supplier")
    after_supplier = _send(client, "Selected 001463", conversation_id, {"action":"select_entity_match","draft_session_id":conversation_id,"table_field":"__parent__","row_id":supplier_row["row_id"],"fieldname":"supplier","selected_value":"001463"})
    resolution = _part(after_supplier, "child_rows_resolution_required")
    oven_row = next(row for row in resolution["rows"] if "oven" in row["query"].lower())
    after_oven = _send(client, "Selected KA-HBEO4-00087", conversation_id, {"action":"select_entity_match","draft_session_id":conversation_id,"table_field":"items","row_id":oven_row["row_id"],"fieldname":"item_code","selected_value":"KA-HBEO4-00087"})
    resolution = _part(after_oven, "child_rows_resolution_required")
    ac_row = next(row for row in resolution["rows"] if "ac" in row["query"].lower() or "midea" in row["query"].lower())
    after_ac = _send(client, "Selected HA-MSA1-00045", conversation_id, {"action":"select_entity_match","draft_session_id":conversation_id,"table_field":"items","row_id":ac_row["row_id"],"fieldname":"item_code","selected_value":"HA-MSA1-00045"})
    options = _part(after_ac, "draft_field_options")
    return _send(client, "Selected POM Warehouse - CTS", conversation_id, {"action":"select_draft_field_value","draft_session_id":conversation_id,"table_field":"items","row_ids":options["row_ids"],"fieldname":"warehouse","selected_value":"POM Warehouse - CTS"})


def test_business_abbreviation_normalization():
    assert normalize_business_abbreviations("create po for bnbm") == "create purchase order for bnbm"
    assert normalize_business_abbreviations("create PI") == "create purchase invoice"


def test_create_po_routes_to_draft_not_blocked_write(client):
    data = _send(client, "create po for bnbm")

    assert data["intent"] in {"child_rows_resolution_required", "crud_create"}
    assert data["current_state"] in {"DRAFT_ENTITY_RESOLUTION", "DRAFT_INFORMATION_REQUIRED", "DRAFT_COLLECTING"}
    assert data["response_type"] in {"entity_selection", "draft_information_required", "crud_create"}
    assert "blocked" not in data["content"].lower()


def test_every_response_has_state_contract(client):
    data = _send(client, "show customers")

    assert data["current_state"]
    assert data["response_type"]
    assert "available_actions" in data


def test_composite_draft_inspection_and_mutation_refreshes_preview(client):
    preview = _preview_with_two_items(client)
    updated = _send(client, "show UOM and update oven rate to 250", preview["conversation_id"])
    record_preview = _part(updated, "record_preview")
    rows = {row["item_code"]: row for row in record_preview["after_data"]["items"]}

    assert updated["intent"] == "draft_preview_updated"
    assert updated["current_state"] == "DRAFT_PREVIEW"
    assert rows["KA-HBEO4-00087"]["rate"] == 250
    assert rows["KA-HBEO4-00087"]["uom"]


def test_report_followup_uses_report_state(client):
    first = _send(client, "show customers")
    chart = _send(client, "show this result as a chart", first["conversation_id"])

    assert chart["response_type"] == "report_result"
    assert chart["current_state"] == "REPORT_READY"
    assert any(part["type"] == "chart" for part in chart["parts"])


def test_workflow_query_bypasses_active_draft(client):
    draft = _send(client, "create po for bnbm")
    approvals = _send(client, "show my pending approvals", draft["conversation_id"])

    assert approvals["intent"] == "workflow_list_pending"
    assert approvals["response_type"] == "workflow_list_pending"
    assert "draft" not in approvals["content"].lower()


def test_structured_refresh_bypasses_active_draft_state():
    engine = ConversationStateEngine()
    context = ConversationContext(conversation_id="conv-test", active_state=ConversationState.DRAFT_ENTITY_RESOLUTION)
    decision = engine.decide(
        ChatMessageRequest(message="Refresh", structured_action={"action": "refresh_result", "result_type": "pending_approvals"}),
        context,
        has_pending_draft=True,
        has_report=False,
    )

    assert decision.route == "general_router"
    assert "structured result action" in decision.reason


def test_exact_document_detail_bypasses_active_draft_state():
    engine = ConversationStateEngine()
    context = ConversationContext(conversation_id="conv-test", active_state=ConversationState.DRAFT_ENTITY_RESOLUTION)
    decision = engine.decide(
        ChatMessageRequest(message="show detail for Purchase Order PUR-ORD-2026-00608"),
        context,
        has_pending_draft=True,
        has_report=False,
    )

    assert decision.route == "general_router"
    assert decision.reason == "document detail request"
