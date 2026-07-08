def _plan():
    return {
        "title": "Customer Sales Summary",
        "source": {"sourceType": "doctype", "sourceName": "Sales Invoice"},
        "outputMode": "table_chart",
        "groupBy": ["customer"],
        "metrics": [{"fieldname": "grand_total", "function": "sum", "label": "Total Amount"}],
        "chart": {"chartType": "bar"},
        "limit": 100,
    }


def test_save_report_view_stores_config_only(client):
    response = client.post("/api/report-composer/views", json={"name": "Customer Sales Summary", "plan": _plan()})
    assert response.status_code == 200, response.text
    view = response.json()["data"]
    assert view["name"] == "Customer Sales Summary"
    assert "rows" not in view
    assert "rows" not in str(view["plan"]).lower()


def test_export_report_composer_result(client):
    response = client.post("/api/report-composer/export?file_format=csv", json={"plan": _plan()})
    assert response.status_code == 200, response.text
    file_data = response.json()["data"]["file"]
    assert file_data["file_format"] == "csv"
    assert file_data["download_url"].endswith("/download")


def test_pin_report_composer_config(client):
    response = client.post("/api/report-composer/pin-to-dashboard", json={"plan": _plan()})
    assert response.status_code == 200, response.text
    widget = response.json()["data"]
    assert widget["title"] == "Customer Sales Summary"
    assert widget["source"]["source_type"] == "manual_config"
