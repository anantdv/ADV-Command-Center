def test_stock_balance_prompt_maps_to_report(client):
    response = client.post("/api/chat/message", json={"message": "show stock balance"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["intent"] == "run_report"
    assert data["source"]["source_name"] == "Stock Balance"


def test_stock_balance_diagnostic_normalizes_response(client):
    response = client.post("/api/reports/diagnose", json={"report_name": "Stock Balance"})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["method_path"].endswith("ai_command_center.api.reports.run_report")
    assert "from_date" in data["filters_used"]
    assert data["frappe_response_shape"]["has_columns"] is True
