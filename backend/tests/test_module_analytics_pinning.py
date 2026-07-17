from app.utils.analytics_catalog import ANALYTICS_CATALOG


def test_analytics_definitions_support_pin_without_rows():
    definition = ANALYTICS_CATALOG["purchase_orders_by_supplier"]

    pinned_config = {
        "target_type": "module",
        "module_name": definition["module"],
        "source_type": "analytics",
        "analytics_key": definition["key"],
        "date_range_mode": "global",
        "filters": {},
        "chart_type": definition["default_chart"],
        "limit": definition.get("default_limit", 20),
    }

    assert "rows" not in pinned_config
    assert pinned_config["analytics_key"] == "purchase_orders_by_supplier"
