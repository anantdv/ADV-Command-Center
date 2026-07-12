import pytest

from app.services.command_router_service import CommandRouterService


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt", ["show stock balance", "show stock", "show item stock"])
async def test_stock_prompts_route_to_stock_balance(prompt):
    intent = await CommandRouterService().route(prompt)
    assert intent.intent == "run_report"
    assert intent.report_name == "Stock Balance"
    assert intent.module_context == "Stock"
    assert intent.source == "hard_rule"


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt", ["show receivables", "show customer outstanding"])
async def test_receivable_prompts_route_to_accounts_receivable(prompt):
    intent = await CommandRouterService().route(prompt)
    assert intent.intent == "run_report"
    assert intent.report_name == "Accounts Receivable"


@pytest.mark.asyncio
async def test_payables_route_to_accounts_payable():
    intent = await CommandRouterService().route("show payables")
    assert intent.intent == "run_report"
    assert intent.report_name == "Accounts Payable"
