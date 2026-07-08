import pytest

from app.services.query_planner_service import QueryPlannerService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prompt", "doctype", "expected_filters"),
    [
        ("show me the customer name Nuar Urpa", "Customer", {"customer_name": ["like", "%Nuar Urpa%"]}),
        ("show customer Nuar Urpa", "Customer", {"customer_name": ["like", "%Nuar Urpa%"]}),
        ("find customer called Nuar Urpa", "Customer", {"customer_name": ["like", "%Nuar Urpa%"]}),
        ("show me supplier name Pacific Hardware", "Supplier", {"supplier_name": ["like", "%Pacific Hardware%"]}),
        ("show suppliers from Fiji", "Supplier", {"country": "Fiji"}),
        ("show items containing laptop", "Item", {"item_name": ["like", "%laptop%"]}),
        ("show item laptop", "Item", {"item_name": ["like", "%laptop%"]}),
        ("show product laptop", "Item", {"item_name": ["like", "%laptop%"]}),
        ("show quotations for customer ABC Trading", "Quotation", {"party_name": ["like", "%ABC Trading%"]}),
    ],
)
async def test_query_planner_entity_filters(prompt, doctype, expected_filters):
    plan = await QueryPlannerService().plan(prompt)

    assert plan.intent == "list_records"
    assert plan.doctype == doctype
    for key, value in expected_filters.items():
        assert plan.normalized_filters[key] == value
    assert plan.fields
    assert plan.limit <= 500


@pytest.mark.asyncio
async def test_query_planner_invoice_record_id():
    plan = await QueryPlannerService().plan("show invoice ACC-SINV-2025-00001")

    assert plan.intent == "get_record"
    assert plan.doctype == "Sales Invoice"
    assert plan.record_name == "ACC-SINV-2025-00001"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prompt", "doctype", "expected_filters"),
    [
        ("show me invoices for the month of may 2025", "Sales Invoice", {"posting_date": ["between", ["2025-05-01", "2025-05-31"]]}),
        ("show invoices for may 2025", "Sales Invoice", {"posting_date": ["between", ["2025-05-01", "2025-05-31"]]}),
        ("show unpaid invoices for may 2025", "Sales Invoice", {"status": ["in", ["Unpaid", "Overdue"]], "posting_date": ["between", ["2025-05-01", "2025-05-31"]]}),
        ("show unpaid purchase invoices for may 2025", "Purchase Invoice", {"status": ["in", ["Unpaid", "Overdue"]], "posting_date": ["between", ["2025-05-01", "2025-05-31"]]}),
        ("show purchase orders valued between 40000 to 50000", "Purchase Order", {"grand_total": ["between", [40000, 50000]]}),
        ("show sales invoices above 50000", "Sales Invoice", {"grand_total": [">", 50000]}),
        ("show purchase invoices below 10000", "Purchase Invoice", {"grand_total": ["<", 10000]}),
        ("show sales orders from january 2025 to march 2025", "Sales Order", {"transaction_date": ["between", ["2025-01-01", "2025-03-31"]]}),
    ],
)
async def test_query_planner_date_status_and_value_filters(prompt, doctype, expected_filters):
    plan = await QueryPlannerService().plan(prompt)

    assert plan.intent == "list_records"
    assert plan.doctype == doctype
    for key, value in expected_filters.items():
        assert plan.normalized_filters[key] == value
    assert plan.fields
