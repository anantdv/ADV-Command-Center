import pytest

from app.utils.analytics_plan_builder import AnalyticsPlanBuilder


@pytest.mark.parametrize(
    ("prompt", "key"),
    [
        ("show monthly sales trend for 2025", "monthly_sales_trend"),
        ("show top 10 customers by outstanding", "top_customers_by_outstanding"),
        ("show purchase orders by supplier", "purchase_orders_by_supplier"),
        ("show sales orders by status as pie chart", "sales_orders_by_status"),
        ("show quotation value by month for 2025", "quotation_value_by_month"),
        ("show customers by territory", "customers_by_territory"),
        ("show suppliers by country", "suppliers_by_country"),
        ("show items by item group", "items_by_item_group"),
    ],
)
def test_analytics_plan_builder_maps_prompts(prompt, key):
    plan = AnalyticsPlanBuilder().build_from_prompt(prompt)

    assert plan.analytics_key == key
    assert plan.confidence > 0.8


def test_analytics_plan_extracts_top_n_and_chart():
    plan = AnalyticsPlanBuilder().build_from_prompt("show top 10 customers by outstanding as bar chart")

    assert plan.limit == 10
    assert plan.chart_type == "bar"
