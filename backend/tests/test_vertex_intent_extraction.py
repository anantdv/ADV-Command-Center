import json

import pytest

from app.agents.router_agent import RouterAgent
from app.config import settings
from app.llm.base import BaseLLMProvider, LLMResponse
from app.llm.extraction_service import LLMExtractionService
from app.llm.safety import validate_extracted_intent
from app.llm.schemas import ExtractedIntent
from app.services.chat_service import chat_service


class FakeProvider(BaseLLMProvider):
    def __init__(self,payload): self.payload=payload;self.called=False;self.messages=[]
    async def complete(self,messages,response_schema=None,**kwargs):
        self.called=True;self.messages=messages
        content=self.payload if isinstance(self.payload,str) else json.dumps(self.payload)
        return LLMResponse(content=content,provider="vertex_gemini",model="gemini-test",latency_ms=7)


@pytest.fixture
def llm_enabled(monkeypatch):
    monkeypatch.setattr(settings,"enable_llm_extraction",True)
    monkeypatch.setattr(settings,"extraction_fallback_to_rules",True)
    monkeypatch.setattr(settings,"llm_confidence_threshold",.65)


def payload(**overrides):
    base={"intent":"list_records","operation":"read","doctype":"Customer","report_name":None,"record_name":None,"data":{},"filters":{},"fields":[],"file_format":None,"widget_type":None,"date_range":None,"limit":20,"confidence":.9,"missing_information":[],"blocked_reason":None,"user_facing_summary":"Show customers"}
    return {**base,**overrides}


@pytest.mark.asyncio
async def test_disabled_uses_rule_router(monkeypatch):
    monkeypatch.setattr(settings,"enable_llm_extraction",False)
    result=await RouterAgent().classify("show customers")
    assert result.intent=="list_records" and result.extraction_method=="rules"


@pytest.mark.asyncio
async def test_valid_vertex_json_and_minimal_outbound_payload(llm_enabled):
    provider=FakeProvider(payload(filters={"disabled":0}))
    result=await RouterAgent(LLMExtractionService(provider)).classify("show active customers")
    assert result.extraction_method=="vertex_gemini"
    assert result.filters=={"disabled":0}
    outbound=json.loads(provider.messages[1].content)
    assert set(outbound)=={"user_message","module_context","current_date","allowed_doctypes","allowed_reports","allowed_file_formats","allowed_widget_types"}
    assert "records" not in provider.messages[1].content


@pytest.mark.asyncio
async def test_invalid_json_falls_back_to_rules(llm_enabled):
    result=await RouterAgent(LLMExtractionService(FakeProvider("not-json"))).classify("show items")
    assert result.intent=="list_records" and result.doctype=="Item" and result.extraction_method=="rules"


@pytest.mark.asyncio
async def test_file_and_dashboard_intents(llm_enabled):
    file_result=await RouterAgent(LLMExtractionService(FakeProvider(payload(intent="generate_file",operation="export",doctype=None,report_name="Accounts Receivable",file_format="pdf")))).classify("generate receivables pdf")
    assert file_result.intent=="generate_file" and file_result.source_type=="report"
    pin=await RouterAgent(LLMExtractionService(FakeProvider(payload(intent="pin_to_dashboard",operation="pin",doctype="Sales Invoice",fields=["customer","outstanding_amount"],widget_type="bar_chart")))).classify("pin top customers")
    assert pin.intent=="pin_to_dashboard" and pin.widget_type=="bar_chart"


def test_safety_removes_sensitive_fields_caps_limit_and_rejects_unknown():
    checked=validate_extracted_intent(ExtractedIntent.model_validate(payload(intent="crud_update",operation="update",data={"territory":"Fiji","docstatus":1,"api_key":"x"},fields=["territory","salary"],limit=900)))
    assert checked.data=={"territory":"Fiji"};assert checked.fields==["territory"];assert checked.limit==500
    unknown=validate_extracted_intent(ExtractedIntent.model_validate(payload(doctype="Secret DocType")))
    assert unknown.intent=="unsupported" and unknown.doctype is None


@pytest.mark.asyncio
async def test_privacy_block_falls_back_without_calling_provider(llm_enabled):
    provider=FakeProvider(payload())
    result=await LLMExtractionService(provider).extract_intent("use token=super-secret")
    assert result is None and provider.called is False


def test_create_customer_extraction_reaches_existing_preview(client,llm_enabled):
    provider=FakeProvider(payload(intent="crud_create",operation="create",doctype="Customer",data={"customer_name":"Blue Ocean Trading","customer_group":"Commercial","territory":"Fiji"}))
    original=chat_service.router
    chat_service.router=RouterAgent(LLMExtractionService(provider))
    try:
        response=client.post("/api/chat/message",json={"message":"create customer Blue Ocean Trading"})
    finally: chat_service.router=original
    assert response.status_code==200,response.text
    data=response.json()["data"]
    assert data["intent"]=="crud_create"
    assert any(part["type"]=="confirmation" for part in data["parts"])
    assert data["extraction"]["method"]=="vertex_gemini"


def test_original_prompt_safety_overrides_bad_model_classification(client,llm_enabled):
    provider=FakeProvider(payload(intent="list_records",operation="read",doctype="Customer",user_facing_summary="Show customers"))
    original=chat_service.router
    chat_service.router=RouterAgent(LLMExtractionService(provider))
    try:
        delete=client.post("/api/chat/message",json={"message":"delete all customers"}).json()["data"]
        payment=client.post("/api/chat/message",json={"message":"create payment entry for customer ABC"}).json()["data"]
    finally: chat_service.router=original
    assert delete["permission"]["allowed"] is False
    assert payment["permission"]["allowed"] is False


def test_debug_endpoint_is_development_only(client,monkeypatch):
    monkeypatch.setattr(settings,"enable_llm_extraction",False)
    monkeypatch.setattr(settings,"app_env","development")
    assert client.post("/api/debug/extract-intent",json={"message":"show customers"}).status_code==200
    monkeypatch.setattr(settings,"app_env","production")
    assert client.post("/api/debug/extract-intent",json={"message":"show customers"}).status_code==404
