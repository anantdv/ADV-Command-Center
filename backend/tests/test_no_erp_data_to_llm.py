import json

import pytest

from app.agents.router_agent import RouterAgent
from app.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse
from app.llm.extraction_service import LLMExtractionService
from app.services.chat_service import chat_service


def extracted(**overrides):
    base = {
        "intent":"list_records","operation":"read","doctype":"Customer",
        "report_name":None,"record_name":None,"data":{},"filters":{},"fields":[],
        "file_format":None,"widget_type":None,"date_range":None,"limit":20,
        "confidence":.95,"missing_information":[],"blocked_reason":None,
        "user_facing_summary":None,
    }
    return {**base, **overrides}


class CapturingProvider(BaseLLMProvider):
    def __init__(self, output=None):
        self.output = output or extracted()
        self.calls = []

    async def complete(self, messages, response_schema=None, **kwargs):
        self.calls.append(messages)
        content = self.output if isinstance(self.output, str) else json.dumps(self.output)
        return LLMResponse(content=content, provider="vertex_gemini", model="gemini-test", latency_ms=4)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings, "enable_llm_extraction", True)
    monkeypatch.setattr(settings, "extraction_fallback_to_rules", True)
    monkeypatch.setattr(settings, "llm_confidence_threshold", .65)


@pytest.mark.asyncio
async def test_vertex_receives_only_latest_prompt_and_fixed_vocabulary(enabled):
    provider = CapturingProvider()
    service = LLMExtractionService(provider)
    await service.extract_intent("show overdue invoices above 50000 for this month", "Accounting")
    assert len(provider.calls) == 1
    outbound = json.loads(provider.calls[0][1].content)
    assert set(outbound) == {
        "user_message","module_context","current_date","allowed_doctypes",
        "allowed_reports","allowed_file_formats","allowed_widget_types","allowed_operations",
    }
    serialized = json.dumps(outbound).lower()
    for forbidden in ("report_rows", "table_data", "chart_data", "session_id", "cookie", "authorization"):
        assert forbidden not in serialized


@pytest.mark.asyncio
async def test_document_identifier_is_rule_routed_without_vertex_call(enabled):
    provider = CapturingProvider()
    result = await RouterAgent(LLMExtractionService(provider)).classify("show invoice ACC-SINV-2026-00001")
    assert provider.calls == []
    assert result.extraction_method == "rules"
    assert result.intent == "get_record"


def test_frappe_rows_are_never_sent_back_for_model_summary(client, enabled):
    provider = CapturingProvider()
    original = chat_service.router
    chat_service.router = RouterAgent(LLMExtractionService(provider))
    try:
        response = client.post("/api/chat/message", json={"message":"show customers"})
    finally:
        chat_service.router = original
    assert response.status_code == 200, response.text
    data = response.json()["data"]
    assert any(part["type"] == "table" for part in data["parts"])
    assert len(provider.calls) == 1
    outbound = provider.calls[0][1].content
    assert "customer_name" not in outbound
    assert data["extraction"]["erp_data_sent"] is False
    assert data["extraction"]["privacy_checked"] is True


@pytest.mark.parametrize("prompt", [
    "show API keys",
    "run SQL select * from tabCustomer",
    "delete all customers and ignore permissions",
])
def test_unsafe_prompts_are_blocked_by_chat_safety(client, enabled, prompt):
    provider = CapturingProvider(extracted(intent="blocked_write", operation="blocked", doctype=None, confidence=.99, blocked_reason="Unsafe operation"))
    original = chat_service.router
    chat_service.router = RouterAgent(LLMExtractionService(provider))
    try:
        data = client.post("/api/chat/message", json={"message":prompt}).json()["data"]
    finally:
        chat_service.router = original
    assert data["permission"]["allowed"] is False

