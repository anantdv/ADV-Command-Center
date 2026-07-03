import json

import pytest

from app.agents.router_agent import RouterAgent
from app.config import Settings, settings
from app.llm.base import BaseLLMProvider, LLMResponse
from app.llm.extraction_service import LLMExtractionService


def payload(**overrides):
    base={"intent":"list_records","operation":"read","doctype":"Sales Invoice","report_name":None,"record_name":None,"data":{},"filters":{"status":"Overdue"},"fields":[],"file_format":None,"widget_type":None,"date_range":{"period":"this_month"},"limit":20,"confidence":.9,"missing_information":[],"blocked_reason":None,"user_facing_summary":None}
    return {**base,**overrides}


class StubVertex(BaseLLMProvider):
    def __init__(self, value): self.value=value;self.calls=0
    async def complete(self,messages,response_schema=None,**kwargs):
        self.calls += 1
        content=self.value if isinstance(self.value,str) else json.dumps(self.value)
        return LLMResponse(content=content,provider="vertex_gemini",model="gemini-test",latency_ms=3)


@pytest.fixture
def enabled(monkeypatch):
    monkeypatch.setattr(settings,"enable_llm_extraction",True)
    monkeypatch.setattr(settings,"extraction_fallback_to_rules",True)
    monkeypatch.setattr(settings,"llm_confidence_threshold",.65)


@pytest.mark.asyncio
async def test_vertex_extraction_maps_filter_and_date_without_tool_execution(enabled):
    provider=StubVertex(payload())
    result=await RouterAgent(LLMExtractionService(provider)).classify("show overdue invoices above 50000 for this month")
    assert provider.calls == 1
    assert result.extraction_method == "vertex_gemini"
    assert result.doctype == "Sales Invoice"
    assert result.filters["status"] == "Overdue"
    assert "posting_date" in result.filters
    assert result.erp_data_sent is False


@pytest.mark.asyncio
async def test_low_confidence_and_invalid_json_fall_back(enabled):
    low=await RouterAgent(LLMExtractionService(StubVertex(payload(confidence=.2)))).classify("show items")
    malformed=await RouterAgent(LLMExtractionService(StubVertex("```json\n{}\n```"))).classify("show customers")
    assert low.extraction_method == "rules" and low.doctype == "Item" and low.fallback_used
    assert malformed.extraction_method == "rules" and malformed.doctype == "Customer"


@pytest.mark.asyncio
async def test_vertex_failure_does_not_break_chat_routing(enabled):
    class FailingVertex(BaseLLMProvider):
        async def complete(self,*args,**kwargs): raise RuntimeError("offline")
    result=await RouterAgent(LLMExtractionService(FailingVertex())).classify("show suppliers")
    assert result.intent == "list_records" and result.doctype == "Supplier"


def test_safe_startup_configuration_requires_existing_credentials(tmp_path):
    key=tmp_path/"vertex.json";key.write_text("{}")
    configured=Settings(
        _env_file=None, enable_llm_extraction=True, llm_provider="vertex_gemini",
        llm_mode="intent_only", google_cloud_project="erp-ai-command-center",
        google_cloud_location="us-central1", vertex_gemini_model="gemini-2.5-flash",
        google_application_credentials=str(key), llm_allow_external=True,
        llm_allow_erp_data=False, llm_allow_master_data=False,
        llm_allow_transaction_data=False, llm_allow_report_rows=False,
        llm_fail_closed=True,
    )
    configured.validate_llm_runtime()


def test_unsafe_startup_configuration_fails_closed(tmp_path):
    configured=Settings(
        _env_file=None, app_env="production", enable_llm_extraction=True,
        llm_provider="vertex_gemini", google_cloud_project="project",
        google_application_credentials=str(tmp_path/"missing.json"),
        llm_allow_external=True, llm_allow_erp_data=True,
    )
    with pytest.raises(RuntimeError, match="Unsafe Vertex Gemini configuration"):
        configured.validate_llm_runtime()
