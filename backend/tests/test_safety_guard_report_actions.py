import pytest

from app.agents.router_agent import RouterAgent


@pytest.mark.asyncio
async def test_manual_chart_ui_action_needs_context_not_blocked_write():
    intent = await RouterAgent().classify("change chart type")
    assert intent.intent == "unsupported"
    assert intent.write_requested is False
    assert "select a chart" in (intent.missing_info_hint or "").lower()


@pytest.mark.asyncio
async def test_real_unsafe_action_still_blocked():
    intent = await RouterAgent().classify("submit sales invoice ACC-SINV-2026-00122")
    assert intent.intent == "blocked_write"
    assert intent.write_requested is True
