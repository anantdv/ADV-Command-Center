from app.services.entity_resolution_service import EntityResolutionService
from app.utils.payload_builder import PayloadBuilder


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


def test_draft_purchase_order_intent_priority_does_not_list_records(client):
    data = _send(client, "draft a purchase order for abc limited with items soap sunflower qty1, 32inch tv qty2")

    assert data["intent"] in {"child_rows_resolution_required", "crud_create"}
    assert data["intent"] != "list_records"
    assert not any(part["type"] == "table" and part.get("title") == "Purchase Order" for part in data["parts"])


def test_purchase_order_clean_extraction_removes_grammar_words():
    data = PayloadBuilder.extract_create("Purchase Order", "create a purchase order for abc limited with items soap sunflower qty1, 32inch tv qty2")

    assert data["supplier"] == "abc limited"
    assert data["items"][0]["item_query"] == "soap sunflower"
    assert data["items"][0]["qty"] == 1
    assert data["items"][1]["item_query"] == "32 inch tv"
    assert data["items"][1]["qty"] == 2
    assert "items" not in data["items"][0]["item_query"].lower()


def test_new_purchase_order_request_clears_stale_rows(client):
    first = _send(client, "draft a purchase order for abc limited with items soap sunflower qty1, 32inch tv qty2")
    conversation_id = first["conversation_id"]

    second = _send(client, "create a draft purchase order for supplier Zucci for items home basic overn 45l qty 2, media split ac qty1", conversation_id)
    resolution = _part(second, "child_rows_resolution_required")
    queries = " ".join(row["query"] for row in resolution["rows"]).lower()

    assert "zucci" in queries
    assert "home basic oven 45 l" in queries
    assert "midea split ac" in queries
    assert "soap sunflower" not in queries
    assert "32 inch tv" not in queries


def test_proceed_command_does_not_extract_supplier_and(client):
    first = _send(client, "draft a purchase order for abc limited with items soap sunflower qty1")
    data = _send(client, "proceed with selected supplier and item", first["conversation_id"])

    resolution = _part(data, "child_rows_resolution_required")
    assert all(row["query"].lower() != "and" for row in resolution["rows"])


def test_short_correction_refines_matching_unresolved_row(client):
    first = _send(client, "create a draft purchase order for supplier Zucci for items home basic oven 45l qty 2, media split ac qty1")
    data = _send(client, "Midea Split AC", first["conversation_id"])

    resolution = _part(data, "child_rows_resolution_required")
    queries = [row["query"] for row in resolution["rows"]]
    assert "Midea Split AC" in queries


def test_supplier_ranking_penalizes_legal_suffix_only_matches():
    service = EntityResolutionService()
    abc = service._score_row("Supplier", "ABC Limited", {"name": "ABC-LTD", "supplier_name": "ABC Limited", "disabled": 0})
    ast = service._score_row("Supplier", "ABC Limited", {"name": "AST-LTD", "supplier_name": "AST Limited", "disabled": 0})

    assert abc.score >= 0.95
    assert ast.score <= 0.2

def test_purchase_order_preserves_two_items_without_second_qty():
    data = PayloadBuilder.extract_create("Purchase Order", "create a draft purchase order for zucci with item oven 45L and Midea Split ac")

    assert data["supplier"] == "zucci"
    assert len(data["items"]) == 2
    assert data["items"][0]["item_query"].lower() == "oven 45 l"
    assert data["items"][0]["qty"] == 1
    assert data["items"][1]["item_query"] == "Midea Split ac"
    assert data["items"][1]["qty"] == 1


def test_purchase_order_selection_preserves_remaining_rows_and_blocks_preview_for_warehouse(client):
    first = _send(client, "create a draft purchase order for zucci with item oven 45L and Midea Split ac")
    conversation_id = first["conversation_id"]
    resolution = _part(first, "child_rows_resolution_required")
    supplier_row = next(row for row in resolution["rows"] if row["link_field"] == "supplier")
    item_rows = [row for row in resolution["rows"] if row["link_field"] == "item_code"]
    assert len(item_rows) == 2

    after_supplier = _send(client, "Selected 001463", conversation_id, {"action":"select_entity_match","draft_session_id":conversation_id,"table_field":"__parent__","row_id":supplier_row["row_id"],"fieldname":"supplier","selected_value":"001463"})
    supplier_resolution = _part(after_supplier, "child_rows_resolution_required")
    assert len([row for row in supplier_resolution["rows"] if row["link_field"] == "item_code"]) == 2

    oven_row = next(row for row in supplier_resolution["rows"] if "oven" in row["query"].lower())
    after_oven = _send(client, "Selected KA-HBEO4-00087", conversation_id, {"action":"select_entity_match","draft_session_id":conversation_id,"table_field":"items","row_id":oven_row["row_id"],"fieldname":"item_code","selected_value":"KA-HBEO4-00087"})

    assert after_oven["intent"] in {"child_rows_resolution_required", "draft_field_options"}
    assert not any(part["type"] == "record_preview" for part in after_oven["parts"])
    if after_oven["intent"] == "child_rows_resolution_required":
        remaining = _part(after_oven, "child_rows_resolution_required")
        assert any("midea" in row["query"].lower() for row in remaining["rows"])


def test_contextual_warehouse_list_stays_inside_active_draft(client):
    first = _send(client, "create a draft purchase order for zucci with items ITEM-001 qty1")
    conversation_id = first["conversation_id"]
    resolution = _part(first, "child_rows_resolution_required")
    supplier_row = next(row for row in resolution["rows"] if row["link_field"] == "supplier")
    after_supplier = _send(client, "Selected 001463", conversation_id, {"action":"select_entity_match","draft_session_id":conversation_id,"table_field":"__parent__","row_id":supplier_row["row_id"],"fieldname":"supplier","selected_value":"001463"})
    assert after_supplier["intent"] == "draft_field_options"

    warehouses = _send(client, "show me warehouse list", conversation_id)
    options = _part(warehouses, "draft_field_options")
    assert warehouses["intent"] == "draft_field_options"
    assert all(not option["metadata"].get("is_group") for option in options["options"] if not option.get("disabled"))
    assert not any(part["type"] == "table" and part.get("title") == "Warehouse" for part in warehouses["parts"])


def test_warehouse_detail_prompt_routes_to_exact_document(client):
    data = _send(client, "show detail for Warehouse Goods In Transit - CTS")

    assert data["intent"] == "get_record"
    detail = _part(data, "record_detail")
    assert detail["doctype"] == "Warehouse"
    assert detail["name"] == "Goods In Transit - CTS"
    assert not any(part["type"] == "table" and part.get("total_rows", 0) == 9 for part in data["parts"])


def _purchase_order_preview_with_two_items(client):
    first = _send(client, "create a draft purchase order for supplier Zucci for items home basic oven 45l qty 2, midea split ac qty1")
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
    preview = _send(client, "Selected POM Warehouse - CTS", conversation_id, {"action":"select_draft_field_value","draft_session_id":conversation_id,"table_field":"items","row_ids":options["row_ids"],"fieldname":"warehouse","selected_value":"POM Warehouse - CTS"})
    return preview


def test_purchase_order_preview_persists_warehouse_and_uom(client):
    preview_response = _purchase_order_preview_with_two_items(client)
    preview = _part(preview_response, "record_preview")
    rows = preview["after_data"]["items"]

    assert preview_response["intent"] == "crud_create"
    assert {row["item_code"] for row in rows} == {"KA-HBEO4-00087", "HA-MSA1-00045"}
    assert all(row.get("warehouse") == "POM Warehouse - CTS" for row in rows)
    assert all(row.get("uom") == "Nos" for row in rows)
    assert preview.get("draft_session_id") == preview_response["conversation_id"]
    assert preview.get("draft_version") == 1


def test_draft_rate_update_after_preview_regenerates_preview_and_totals(client):
    preview_response = _purchase_order_preview_with_two_items(client)
    conversation_id = preview_response["conversation_id"]
    old_confirmation = _part(preview_response, "confirmation")["confirmation_id"]

    updated = _send(client, "update rate oven 250 and ac 500", conversation_id)
    preview = _part(updated, "record_preview")
    rows = {row["item_code"]: row for row in preview["after_data"]["items"]}
    new_confirmation = _part(updated, "confirmation")["confirmation_id"]

    assert updated["intent"] == "draft_preview_updated"
    assert rows["KA-HBEO4-00087"]["rate"] == 250
    assert rows["KA-HBEO4-00087"]["amount"] == 500
    assert rows["HA-MSA1-00045"]["rate"] == 500
    assert rows["HA-MSA1-00045"]["amount"] == 500
    assert preview["totals"]["grand_total"] == 1000
    assert len(preview["changes"]) == 2
    assert new_confirmation != old_confirmation

    stale = client.post("/api/chat/actions/confirm", json={"confirmation_id": old_confirmation})
    assert stale.status_code == 410


def test_draft_rate_update_does_not_fall_to_blocked_write(client):
    preview_response = _purchase_order_preview_with_two_items(client)
    updated = _send(client, "change oven rate to 250", preview_response["conversation_id"])

    assert updated["intent"] == "draft_preview_updated"
    assert not any("disabled" in part.get("content", "").lower() for part in updated["parts"] if part["type"] == "text")
