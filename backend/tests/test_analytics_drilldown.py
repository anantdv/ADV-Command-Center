from app.services.analytics_catalog_service import AnalyticsCatalogService


def test_drilldown_definition_points_to_correct_doctype():
    definition = AnalyticsCatalogService().get_definition("purchase_orders_by_supplier")

    assert definition.drilldown_doctype == "Purchase Order"
    assert definition.module == "Buying"
