import pytest

from app.services.query_planner_service import QueryPlannerService
from app.utils.aggregation_planner import validate_aggregation_plan
from app.schemas.aggregation import AggregationMetric, AggregationPlan


@pytest.mark.asyncio
async def test_monthly_sales_trend_for_2025_creates_line_chart_plan():
    plan = await QueryPlannerService().plan("show monthly sales trend for 2025")

    assert plan.expects_aggregation is True
    assert plan.aggregation.source_name == "Sales Invoice"
    assert plan.aggregation.time_field == "posting_date"
    assert plan.aggregation.time_grain == "month"
    assert plan.aggregation.chart_type == "line"
    assert plan.aggregation.normalized_filters["posting_date"] == ["between", ["2025-01-01", "2025-12-31"]]


@pytest.mark.asyncio
async def test_top_customers_by_outstanding_creates_invoice_grouping():
    plan = await QueryPlannerService().plan("show top 10 customers by outstanding")

    assert plan.aggregation.source_name == "Sales Invoice"
    assert plan.aggregation.group_by == ["customer"]
    assert plan.aggregation.metrics[0].field == "outstanding_amount"
    assert plan.aggregation.order_by_metric == "outstanding_amount_sum"
    assert plan.aggregation.limit == 10


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prompt", "source", "group_by", "chart"),
    [
        ("show purchase orders by supplier as bar chart", "Purchase Order", ["supplier"], "bar"),
        ("show sales orders by status as pie chart", "Sales Order", ["status"], "pie"),
        ("show quotation value by month for 2025", "Quotation", [], "line"),
        ("show customers by territory", "Customer", ["territory"], "bar"),
        ("show suppliers by country", "Supplier", ["country"], "bar"),
        ("show items by item group", "Item", ["item_group"], "bar"),
    ],
)
async def test_supported_aggregation_prompts(prompt, source, group_by, chart):
    plan = await QueryPlannerService().plan(prompt)

    assert plan.aggregation
    assert plan.aggregation.source_name == source
    assert plan.aggregation.group_by == group_by
    assert plan.aggregation.chart_type == chart


def test_invalid_group_by_field_is_rejected():
    plan = AggregationPlan(
        enabled=True,
        source_name="Sales Invoice",
        group_by=["password"],
        metrics=[AggregationMetric(field="grand_total", function="sum")],
    )
    with pytest.raises(ValueError):
        validate_aggregation_plan(plan)


def test_invalid_metric_field_is_rejected():
    plan = AggregationPlan(
        enabled=True,
        source_name="Sales Invoice",
        group_by=["customer"],
        metrics=[AggregationMetric(field="api_secret", function="sum")],
    )
    with pytest.raises(ValueError):
        validate_aggregation_plan(plan)
