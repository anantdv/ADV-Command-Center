from app.schemas.aggregation import AggregationMetric, AggregationPlan
from app.utils.aggregation_engine import AggregationEngine


def test_aggregation_engine_groups_and_sums():
    rows = [
        {"customer": "A", "grand_total": 100},
        {"customer": "A", "grand_total": 50},
        {"customer": "B", "grand_total": 80},
    ]
    plan = AggregationPlan(enabled=True, source_name="Sales Invoice", group_by=["customer"], metrics=[AggregationMetric(field="grand_total", function="sum")], order_by_metric="grand_total_sum")

    result = AggregationEngine().aggregate(rows, plan)

    assert result[0] == {"customer": "A", "grand_total_sum": 150}
    assert result[1] == {"customer": "B", "grand_total_sum": 80}


def test_aggregation_engine_monthly_time_series():
    rows = [
        {"posting_date": "2025-01-10", "grand_total": 100},
        {"posting_date": "2025-01-20", "grand_total": 50},
        {"posting_date": "2025-02-01", "grand_total": 80},
    ]
    plan = AggregationPlan(enabled=True, source_name="Sales Invoice", time_field="posting_date", time_grain="month", metrics=[AggregationMetric(field="grand_total", function="sum")], order_by_metric=None, chart_type="line")

    result = AggregationEngine().aggregate(rows, plan)

    assert result == [
        {"period": "Jan 2025", "grand_total_sum": 150},
        {"period": "Feb 2025", "grand_total_sum": 80},
    ]


def test_aggregation_engine_uses_unknown_for_blank_group():
    rows = [{"status": None, "name": "A"}, {"status": "", "name": "B"}]
    plan = AggregationPlan(enabled=True, source_name="Sales Order", group_by=["status"], metrics=[AggregationMetric(field="name", function="count")], order_by_metric="name_count")

    result = AggregationEngine().aggregate(rows, plan)

    assert result == [{"status": "Unknown", "name_count": 2}]
