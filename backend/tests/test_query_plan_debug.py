from fastapi.testclient import TestClient

from app.main import app


def test_query_plan_debug_customer_name():
    client = TestClient(app)
    response = client.post("/api/debug/query-plan", json={"message": "show me the customer name Nuar Urpa"})

    assert response.status_code == 200
    payload = response.json()["data"]
    plan = payload["query_plan"]
    assert plan["doctype"] == "Customer"
    assert plan["normalized_filters"]["customer_name"] == ["like", "%Nuar Urpa%"]
    assert payload["privacy_checked"] is False


def test_query_plan_debug_invoice_month():
    client = TestClient(app)
    response = client.post("/api/debug/query-plan", json={"message": "show me invoices for the month of may 2025"})

    assert response.status_code == 200
    plan = response.json()["data"]["query_plan"]
    assert plan["doctype"] == "Sales Invoice"
    assert plan["normalized_filters"]["posting_date"] == ["between", ["2025-05-01", "2025-05-31"]]
