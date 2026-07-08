import pytest

from app.utils.report_composer_planner import ReportComposerPlanner


@pytest.mark.asyncio
async def test_plan_sales_invoice_by_customer_report():
    plan = await ReportComposerPlanner().plan_from_message(
        "create a report showing sales invoices by customer for May 2025 with customer, invoice count, total amount, and outstanding amount"
    )
    assert plan.source.source_name == "Sales Invoice"
    assert plan.group_by == ["customer"]
    assert plan.date_range == {"from_date": "2025-05-01", "to_date": "2025-05-31"}
    assert {(metric.fieldname, metric.function) for metric in plan.metrics} >= {
        ("name", "count"),
        ("grand_total", "sum"),
        ("outstanding_amount", "sum"),
    }
    assert plan.chart.chart_type == "bar"


@pytest.mark.asyncio
async def test_multi_source_prompt_returns_limitation_plan():
    plan = await ReportComposerPlanner().plan_from_message("make a monthly sales and purchase comparison for 2025")
    assert "multi_source_disabled" in plan.missing_information
    assert "Multi-source" in plan.warnings[0]


@pytest.mark.asyncio
async def test_amount_between_filter_maps_to_grand_total():
    plan = await ReportComposerPlanner().plan_from_message("show quotations between 10000 and 20000")
    assert plan.source.source_name == "Quotation"
    assert plan.filters[0].fieldname == "grand_total"
    assert plan.filters[0].operator == "between"
