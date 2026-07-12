import pytest

from app.services.command_router_service import CommandRouterService
from app.utils.context_isolation import should_use_previous_context


@pytest.mark.asyncio
async def test_stock_balance_ignores_previous_customer_context():
    previous = {"doctype": "Customer", "name": "C13086"}
    intent = await CommandRouterService().route("show stock balance", previous_context=previous)
    assert intent.intent == "run_report"
    assert intent.report_name == "Stock Balance"
    assert intent.uses_previous_result is False
    assert intent.record_name is None
    assert intent.doctype is None


def test_only_explicit_references_use_previous_context():
    assert should_use_previous_context("open this invoice") is True
    assert should_use_previous_context("pin this") is True
    assert should_use_previous_context("show stock balance") is False
    assert should_use_previous_context("generate sales chart") is False
