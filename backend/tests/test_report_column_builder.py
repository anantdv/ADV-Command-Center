def test_available_columns_for_sales_invoice(client):
    response = client.get("/api/reports/available-columns", params={"source_type": "doctype", "source_name": "Sales Invoice"})
    assert response.status_code == 200
    columns = response.json()["data"]
    assert {"name", "customer", "posting_date"}.issubset({column["key"] for column in columns})


def test_run_report_with_selected_columns(client):
    response = client.post("/api/reports/run-with-columns", json={
        "source_type": "doctype",
        "source_name": "Sales Invoice",
        "columns": ["name", "customer", "status"],
        "filters": {"status": "Overdue"},
        "limit": 10,
    })
    assert response.status_code == 200
    data = response.json()["data"]
    assert [column["key"] for column in data["columns"]] == ["name", "customer", "status"]
    assert set(data["rows"][0]).issubset({"name", "customer", "status"})


def test_sensitive_columns_blocked(client):
    response = client.post("/api/reports/run-with-columns", json={
        "source_type": "doctype",
        "source_name": "Customer",
        "columns": ["name", "api_secret"],
    })
    assert response.status_code == 422
