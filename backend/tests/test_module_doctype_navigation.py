def ok(response):
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_selling_doctype_navigation_contains_standard_selling_doctypes(client):
    data = ok(client.get("/api/modules/Selling/doctypes"))
    doctypes = {item["doctype"]: item for item in data["doctypes"]}

    assert data["moduleName"] == "Selling"
    assert "Customer" in doctypes
    assert "Sales Invoice" in doctypes
    assert doctypes["Sales Invoice"]["route"] == "/modules/selling/doctype/Sales Invoice"
    assert doctypes["Customer"]["canRead"] is True


def test_module_doctype_list_rows_include_click_metadata(client):
    data = ok(client.get("/api/modules/Selling/doctype/Sales%20Invoice/records?page=1&page_size=5"))

    assert data["moduleName"] == "Selling"
    assert data["doctype"] == "Sales Invoice"
    assert data["columns"]
    assert data["rows"]
    assert data["rows"][0]["_meta"]["doctype"] == "Sales Invoice"
    assert data["rows"][0]["_meta"]["clickable"] is True


def test_module_doctype_list_search_and_pagination(client):
    data = ok(client.get("/api/modules/Selling/doctype/Customer/records?page=1&page_size=1&search=Aster"))

    assert data["page"] == 1
    assert data["pageSize"] == 1
    assert data["total"] >= 1
    assert len(data["rows"]) == 1


def test_module_doctype_list_rejects_doctype_outside_module(client):
    response = client.get("/api/modules/Selling/doctype/Salary%20Slip/records")

    assert response.status_code == 404
