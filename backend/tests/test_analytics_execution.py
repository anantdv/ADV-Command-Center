from fastapi.testclient import TestClient

from app.main import app


def test_run_top_customers_analytics():
    client = TestClient(app)
    response = client.post("/api/analytics/run", json={"analytics_key": "top_customers_by_outstanding", "limit": 10, "chart_type": "bar"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analyticsKey"] == "top_customers_by_outstanding"
    assert data["chart"]["chart_type"] == "bar"
    assert isinstance(data["rows"], list)


def test_analytics_plan_endpoint():
    client = TestClient(app)
    response = client.post("/api/analytics/plan", json={"message": "show sales orders by status as pie chart"})

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["analyticsKey"] == "sales_orders_by_status"
    assert data["chartType"] == "pie"
