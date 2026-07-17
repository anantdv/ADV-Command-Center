from app.services.analytics_catalog_service import AnalyticsCatalogService
from app.utils.analytics_catalog import ANALYTICS_CATALOG


def test_buying_catalog_includes_purchase_trend():
    assert "purchase_trend" in ANALYTICS_CATALOG
    assert ANALYTICS_CATALOG["purchase_trend"]["module"] == "Buying"


def test_module_catalog_filters_buying():
    catalog = AnalyticsCatalogService().list_catalog("Buying")

    assert {item.key for item in catalog} >= {"purchase_trend", "purchase_orders_by_supplier", "unpaid_purchase_invoices"}
    assert all(item.module == "Buying" for item in catalog)
