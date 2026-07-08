def post_prompt(client, message: str) -> dict:
    response = client.post("/api/chat/message", json={"message": message})
    assert response.status_code == 200, response.text
    return response.json()["data"]


def test_unpaid_invoices_for_may_2025_prompt(client):
    data = post_prompt(client, "show unpaid invoices for may 2025")
    assert data["source"]["source_name"] == "Sales Invoice"
    assert data["source"]["filters"]["status"] == ["in", ["Unpaid", "Overdue"]]
    assert data["source"]["filters"]["posting_date"] == ["between", ["2025-05-01", "2025-05-31"]]


def test_unpaid_purchase_invoices_for_may_2025_prompt(client):
    data = post_prompt(client, "show unpaid purchase invoices for may 2025")
    assert data["source"]["source_name"] == "Purchase Invoice"
    assert data["source"]["filters"]["status"] == ["in", ["Unpaid", "Overdue"]]
    assert data["source"]["filters"]["posting_date"] == ["between", ["2025-05-01", "2025-05-31"]]


def test_purchase_orders_value_between_prompt(client):
    data = post_prompt(client, "show purchase orders valued between 40000 to 50000")
    assert data["source"]["source_name"] == "Purchase Order"
    assert data["source"]["filters"]["grand_total"] == ["between", [40000.0, 50000.0]]


def test_sales_invoices_above_value_prompt(client):
    data = post_prompt(client, "show sales invoices above 50000")
    assert data["source"]["source_name"] == "Sales Invoice"
    assert data["source"]["filters"]["grand_total"] == [">", 50000.0]


def test_purchase_invoices_below_value_prompt(client):
    data = post_prompt(client, "show purchase invoices below 10000")
    assert data["source"]["source_name"] == "Purchase Invoice"
    assert data["source"]["filters"]["grand_total"] == ["<", 10000.0]


def test_sales_orders_january_to_march_prompt(client):
    data = post_prompt(client, "show sales orders from january 2025 to march 2025")
    assert data["source"]["source_name"] == "Sales Order"
    assert data["source"]["filters"]["transaction_date"] == ["between", ["2025-01-01", "2025-03-31"]]


def test_debug_normalize_filters(client):
    response = client.post("/api/debug/normalize-filters", json={
        "doctype": "Sales Invoice",
        "message": "show unpaid invoices for may 2025",
        "filters": {"status": "unpaid"},
    })
    assert response.status_code == 200
    assert response.json()["data"]["normalized_filters"]["posting_date"] == ["between", ["2025-05-01", "2025-05-31"]]
