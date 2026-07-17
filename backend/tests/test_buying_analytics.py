from app.utils.analytics_catalog import ANALYTICS_CATALOG


def test_purchase_orders_by_supplier_definition():
    definition = ANALYTICS_CATALOG["purchase_orders_by_supplier"]

    assert definition["source_name"] == "Purchase Order"
    assert definition["group_by"] == ["supplier"]
    assert definition["drilldown_doctype"] == "Purchase Order"


def test_unpaid_purchase_invoices_applies_status_filter():
    definition = ANALYTICS_CATALOG["unpaid_purchase_invoices"]

    assert definition["filters"]["status"] == ["in", ["Unpaid", "Overdue"]]
