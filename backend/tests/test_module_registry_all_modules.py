from app.utils.module_doctype_registry import module_doctypes
from app.utils.module_registry import MODULE_REGISTRY, normalize_module_name


EXPECTED = {"Selling", "Buying", "Stock", "Accounts", "CRM", "Projects", "Support", "HR", "Assets", "Manufacturing"}


def ok(response):
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["success"] is True
    return body["data"]


def test_module_registry_contains_all_workspace_modules():
    assert EXPECTED.issubset(set(MODULE_REGISTRY))
    assert normalize_module_name("accounting") == "Accounts"
    assert normalize_module_name("helpdesk") == "Support"


def test_doctype_registry_has_configs_for_all_workspace_modules():
    for module in EXPECTED:
        configs = module_doctypes(module)
        assert configs, module
        for item in configs:
            assert item["doctype"]
            assert item["label"]
            assert item["default_fields"]
            assert item["search_fields"]


def test_module_dashboards_load_for_all_modules_in_mock_mode(client):
    for module in EXPECTED:
        data = ok(client.get(f"/api/modules/{module}/dashboard"))
        assert data["moduleName"] == module
        assert data["doctypes"]
        assert data["kpis"]
        assert "pinnedWidgets" in data


def test_module_doctype_navigation_loads_for_all_modules_in_mock_mode(client):
    for module in EXPECTED:
        data = ok(client.get(f"/api/modules/{module}/doctypes"))
        assert data["moduleName"] == module
        assert data["doctypes"]


def test_module_pinned_widgets_endpoint_loads(client):
    data = ok(client.get("/api/modules/Buying/pinned-widgets"))
    assert isinstance(data, list)


def test_module_record_detail_endpoint_validates_module_doctype(client):
    data = ok(client.get("/api/modules/Buying/doctype/Purchase%20Order/records/PUR-ORD-2026-0001"))
    assert data["doctype"] == "Purchase Order"
    assert data["name"] == "PUR-ORD-2026-0001"

    response = client.get("/api/modules/Buying/doctype/Sales%20Invoice/records/SINV-0001")
    assert response.status_code == 404
