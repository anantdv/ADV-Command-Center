def _send(client, message: str, module_context: str = "Selling"):
    response = client.post("/api/chat/message", json={"message": message, "module_context": module_context})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_selling_context_resolves_invoices_to_sales_invoice(client):
    data = _send(client, "show invoices")
    assert data["source"]["source_name"] == "Sales Invoice"


def test_selling_context_resolves_orders_to_sales_order(client):
    data = _send(client, "show orders")
    assert data["source"]["source_name"] == "Sales Order"


def test_selling_context_pending_approvals_uses_workflow(client):
    data = _send(client, "show pending approvals")
    assert data["intent"] == "workflow_list_pending"
    assert "ERPNext queries such as" not in data["content"]
