from fastapi.testclient import TestClient

from app.main import app
from app.utils.analytics_catalog import ANALYTICS_CATALOG


def test_analytics_catalog_contains_core_reports():
    assert "monthly_sales_trend" in ANALYTICS_CATALOG
    assert "top_customers_by_outstanding" in ANALYTICS_CATALOG
    assert "items_by_item_group" in ANALYTICS_CATALOG


def test_analytics_catalog_endpoint():
    client = TestClient(app)
    response = client.get("/api/analytics/catalog")

    assert response.status_code == 200
    assert "monthly_sales_trend" in response.json()["data"]
