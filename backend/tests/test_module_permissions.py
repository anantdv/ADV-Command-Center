def test_modules_list_only_accessible_modules(client):
    response = client.get("/api/modules")
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert data
    assert all(item["permissions"]["canRead"] for item in data)


def test_selling_module_is_available_in_mock_mode(client):
    response = client.get("/api/modules")
    modules = {item["slug"]: item for item in response.json()["data"]}
    assert "selling" in modules
    assert modules["selling"]["metric"]
