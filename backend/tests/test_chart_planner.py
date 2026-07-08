from app.schemas.aggregation import AggregationMetric, AggregationPlan
from app.utils.chart_plan_builder import build_chart_from_aggregation


def test_bar_chart_contract_from_aggregation():
    plan = AggregationPlan(enabled=True, source_name="Sales Invoice", group_by=["customer"], metrics=[AggregationMetric(field="outstanding_amount", function="sum", label="Outstanding")], order_by_metric="outstanding_amount_sum", chart_type="bar", chart_title="Top Customers")
    rows = [{"customer": "A", "outstanding_amount_sum": 100}]

    chart = build_chart_from_aggregation(rows, plan)

    assert chart["chart_type"] == "bar"
    assert chart["x_key"] == "customer"
    assert chart["y_key"] == "outstanding_amount_sum"
    assert chart["series"][0]["label"] == "Outstanding"
    assert chart["data"] == rows


def test_pie_chart_contract_from_aggregation():
    plan = AggregationPlan(enabled=True, source_name="Sales Order", group_by=["status"], metrics=[AggregationMetric(field="name", function="count")], order_by_metric="name_count", chart_type="pie")
    rows = [{"status": "Open", "name_count": 5}]

    chart = build_chart_from_aggregation(rows, plan)

    assert chart["chart_type"] == "pie"
    assert chart["name_key"] == "status"
    assert chart["value_key"] == "name_count"
