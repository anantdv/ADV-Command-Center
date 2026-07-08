import pytest

from app.agents.router_agent import RouterAgent
from app.schemas.chat import ChatMessageRequest
from app.services.chat_service import ChatService


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("prompt", "doctype", "filters"),
    [
        ("show me the customer name Nuar Urpa", "Customer", {"customer_name": ["like", "%Nuar Urpa%"]}),
        ("show unpaid invoices for may 2025", "Sales Invoice", {"status": ["in", ["Unpaid", "Overdue"]], "posting_date": ["between", ["2025-05-01", "2025-05-31"]]}),
        ("show purchase orders valued between 40000 to 50000", "Purchase Order", {"grand_total": ["between", [40000, 50000]]}),
        ("show quotations for customer ABC Trading", "Quotation", {"party_name": ["like", "%ABC Trading%"]}),
    ],
)
async def test_router_uses_query_planner_for_flexible_read_prompts(prompt, doctype, filters):
    intent = await RouterAgent().classify(prompt)

    assert intent.intent == "list_records"
    assert intent.doctype == doctype
    for key, value in filters.items():
        assert intent.filters[key] == value


@pytest.mark.asyncio
async def test_chat_returns_structured_response_for_customer_name_prompt():
    response = await ChatService().send_chat_message(ChatMessageRequest(message="show me the customer name Nuar Urpa"))

    assert response.intent == "list_records"
    assert response.source
    assert response.source.source_name == "Customer"
    assert response.source.filters["customer_name"] == ["like", "%Nuar Urpa%"]
    assert any(part.type == "table" for part in response.parts)


@pytest.mark.asyncio
async def test_router_preserves_controlled_crud_workflow():
    intent = await RouterAgent().classify("create customer ABC Trading")

    assert intent.intent == "crud_create"
    assert intent.doctype == "Customer"
