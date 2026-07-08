import pytest

from app.services.query_planner_service import QueryPlannerService
from app.utils.aggregation_planner import validate_aggregation_plan
from app.schemas.aggregation import AggregationMetric, AggregationPlan


@pytest.mark.asyncio
async def test_raw_sql_attempt_is_blocked_before_aggregation():
    plan = await QueryPlannerService().plan("show sales by customer; select * from tabSales Invoice")

    assert plan.intent == "unsupported"
    assert plan.blocked_reason


def test_aggregation_does_not_allow_arbitrary_group_or_metric():
    with pytest.raises(ValueError):
        validate_aggregation_plan(AggregationPlan(enabled=True, source_name="Customer", group_by=["api_key"], metrics=[AggregationMetric(field="name", function="count")]))
    with pytest.raises(ValueError):
        validate_aggregation_plan(AggregationPlan(enabled=True, source_name="Customer", group_by=["territory"], metrics=[AggregationMetric(field="salary", function="sum")]))


@pytest.mark.asyncio
async def test_aggregation_plan_contains_no_rows_for_llm():
    plan = await QueryPlannerService().plan("show top 10 customers by outstanding")

    dumped = plan.model_dump(mode="json")
    assert "rows" not in dumped
    assert "records" not in dumped
    assert plan.aggregation is not None
