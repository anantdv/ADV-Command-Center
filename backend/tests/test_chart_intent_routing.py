import pytest

from app.services.command_router_service import CommandRouterService


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt", ["generate sales chart", "show sales chart", "show sales trend", "show monthly sales"])
async def test_sales_chart_prompts_route_to_monthly_sales(prompt):
    intent = await CommandRouterService().route(prompt)
    assert intent.intent == "generate_chart"
    assert intent.analytics_key == "monthly_sales_trend"
    assert intent.chart_requested is True
    assert intent.chart_type == "line"


@pytest.mark.asyncio
async def test_top_customers_routes_to_analytics():
    intent = await CommandRouterService().route("show top customers")
    assert intent.intent == "run_analytics"
    assert intent.analytics_key == "top_customers_by_sales"
    assert intent.chart_requested is True


@pytest.mark.asyncio
async def test_purchase_orders_by_supplier_routes_to_analytics():
    intent = await CommandRouterService().route("show purchase orders by supplier")
    assert intent.intent == "run_analytics"
    assert intent.analytics_key == "purchase_orders_by_supplier"
