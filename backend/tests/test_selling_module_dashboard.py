def test_selling_dashboard_returns_cards_reports_and_recent_documents(client):
    response = client.get("/api/modules/Selling/dashboard")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data["moduleName"] == "Selling"
    assert data["kpis"]
    assert data["reports"]
    assert data["recentDocuments"]
    assert data["quickActions"]


def test_selling_dashboard_contains_expected_kpis(client):
    data = client.get("/api/modules/Selling/dashboard").json()["data"]
    labels = {item["label"] for item in data["kpis"]}
    assert "Total Customers" in labels
    assert "Sales This Month" in labels
    assert "Overdue Sales Invoices" in labels
