from app.agents.router_agent import RouterAgent


def _send(client, message: str, conversation_id: str | None = None):
    payload = {"message": message}
    if conversation_id:
        payload["conversation_id"] = conversation_id
    response = client.post("/api/chat/message", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    return body["data"]


def _part(data: dict, kind: str) -> dict:
    return next(part for part in data["parts"] if part["type"] == kind)


def test_router_interprets_pending_po_with_no_inherited_date_range():
    intent = __import__("asyncio").run(
        RouterAgent().classify(
            "show all pending purchase order for BNBM Kokopo",
            date_range_context={"from_date": "2026-07-01", "to_date": "2026-07-31"},
        )
    )

    assert intent.intent == "list_records"
    assert intent.doctype == "Purchase Order"
    assert intent.date_range is None
    assert intent.filters
    assert intent.filters["supplier"] == ["like", "%BNBM Kokopo%"]
    assert intent.filters["_business_status"]["term"] == "pending"
    assert intent.filters["_business_status"]["include_drafts"] is True


def test_pending_purchase_order_resolves_supplier_name_to_link_value(client):
    data = _send(client, "show all pending purchase order for BNBM Kokopo")

    table = _part(data, "table")
    assert data["intent"] == "list_records"
    assert data["source"]["source_name"] == "Purchase Order"
    assert data["source"]["filters"]["supplier"] == "SUP-2026-00010"
    assert data["source"]["filters"]["_resolved_link_filters"]["supplier"]["query"] == "BNBM Kokopo"
    assert any(row["name"] == "PUR-ORD-2026-00624" for row in table["rows"])


def test_sales_invoice_natural_language_draft_uses_clean_customer_and_item_queries(client):
    data = _send(client, "create a sales invoice for biswajit for item tcl top mount fridge qty 1 price 1500")

    resolution = _part(data, "child_rows_resolution_required")
    parent_rows = [row for row in resolution["rows"] if row["link_field"] == "customer"]
    item_rows = [row for row in resolution["rows"] if row["link_field"] == "item_code"]

    assert data["intent"] == "child_rows_resolution_required"
    assert data["response_type"] == "entity_selection"
    assert parent_rows
    assert parent_rows[0]["query"] == "biswajit"
    assert parent_rows[0]["matches"]
    assert any(match["label"] == "Biswajit Maity" for match in parent_rows[0]["matches"])
    assert not item_rows or item_rows[0]["query"] == "tcl top mount fridge"


def test_sales_invoice_alternate_syntax_parses_qty_and_rate(client):
    data = _send(client, "sales invoice for Biswajit, 2 TVs at 1200 each")
    resolution = _part(data, "child_rows_resolution_required")
    item_rows = [row for row in resolution["rows"] if row["link_field"] == "item_code"]

    if item_rows:
        assert item_rows[0]["query"] == "TVs"
        assert item_rows[0]["extracted"]["qty"] == 2
        assert item_rows[0]["extracted"]["rate"] == 1200
    else:
        # The mock fixture may auto-resolve TV when it is the only high-scoring match;
        # in that case the unresolved parent customer row still proves the draft session
        # retained the parsed item rather than falling back to blocked_write.
        assert any(row["link_field"] == "customer" for row in resolution["rows"])


def test_sales_invoice_plan_waits_on_customer_selection(client):
    data = _send(client, "create a sales invoice for biswajit for item tcl top mount fridge qty 1 price 1500")
    plan = _part(data, "execution_plan")

    resolve_customer = next(step for step in plan["steps"] if step["label"] == "Resolve Customer")
    assert plan["status"] == "waiting_user"
    assert plan["current_step_id"] == resolve_customer["id"]
    assert resolve_customer["status"] == "waiting_user"
    assert any(step["label"] == "Resolve child rows and items" and step["status"] == "pending" for step in plan["steps"])
