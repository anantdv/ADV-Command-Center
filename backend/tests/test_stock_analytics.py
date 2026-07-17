from app.utils.analytics_catalog import ANALYTICS_CATALOG


def test_stock_catalog_includes_standard_reports():
    assert ANALYTICS_CATALOG["stock_balance"]["source_type"] == "standard_report"
    assert ANALYTICS_CATALOG["stock_balance"]["source_name"] == "Stock Balance"
    assert ANALYTICS_CATALOG["stock_ledger"]["source_name"] == "Stock Ledger"


def test_items_by_item_group_drills_to_item():
    assert ANALYTICS_CATALOG["items_by_item_group"]["drilldown_doctype"] == "Item"
