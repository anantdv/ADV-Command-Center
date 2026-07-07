from app.utils.chart_builder import normalize_chart_widget_data


def test_bar_chart_widget_normalized_contract(client):
    response = client.post("/api/dashboard/widgets/debug-chart", json={"widget_type": "bar_chart", "rows": [{"status": "Paid", "count": 4}]})
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["data"] == [{"label": "Paid", "value": 4.0}]
    assert data["chart_config"]["chart_type"] == "bar"


def test_empty_chart_data_handled():
    normalized = normalize_chart_widget_data("pie_chart", [])
    assert normalized["data"] == []
    assert normalized["chart_config"]["chart_type"] == "pie"
