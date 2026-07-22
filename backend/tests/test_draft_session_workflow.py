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
