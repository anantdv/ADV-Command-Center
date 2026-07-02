import json
from datetime import date

from pydantic import ValidationError

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.core.exceptions import AppError
from app.llm.base import BaseLLMProvider, LLMMessage
from app.llm.privacy_gateway import PrivacyGateway
from app.llm.prompts import ALLOWED_DOCTYPES, ALLOWED_FILE_FORMATS, ALLOWED_REPORTS, ALLOWED_WIDGET_TYPES, build_intent_extraction_system_prompt
from app.llm.provider_factory import get_llm_provider
from app.llm.safety import validate_extracted_intent
from app.llm.schemas import ExtractedIntent, get_extracted_intent_json_schema


class LLMExtractionService:
    def __init__(self, provider: BaseLLMProvider | None = None, privacy: PrivacyGateway | None = None):
        self._provider=provider;self.privacy=privacy or PrivacyGateway()

    async def extract_intent(self, user_message: str, module_context: str | None = None, current_date: str | None = None, user: str = "unknown", conversation_id: str | None = None) -> ExtractedIntent | None:
        if not settings.enable_llm_extraction: return None
        provider=self._provider or get_llm_provider()
        if provider is None: return None
        payload={"user_message":user_message,"module_context":module_context,"current_date":current_date or date.today().isoformat(),"allowed_doctypes":ALLOWED_DOCTYPES,"allowed_reports":ALLOWED_REPORTS,"allowed_file_formats":ALLOWED_FILE_FORMATS,"allowed_widget_types":ALLOWED_WIDGET_TYPES}
        check=self.privacy.check_outbound_payload(payload)
        if not check.allowed:
            await self._audit("llm_privacy_blocked",allowed=False,privacy_blocked=True,output=",".join(check.detected_categories),user=user,conversation_id=conversation_id)
            if settings.extraction_fallback_to_rules: return None
            raise AppError(check.reason or "LLM privacy gateway blocked the request.", 422)
        await self._audit("llm_extraction_started",allowed=True,user=user,conversation_id=conversation_id)
        safe_payload=check.redacted_payload or payload
        messages=[LLMMessage(role="system",content=build_intent_extraction_system_prompt()),LLMMessage(role="user",content=json.dumps(safe_payload,separators=(",",":")))]
        try:
            response=await provider.complete(messages,get_extracted_intent_json_schema())
            parsed=json.loads(response.content)
            intent=validate_extracted_intent(ExtractedIntent.model_validate(parsed))
            intent.extraction_method="vertex_gemini";intent.provider=response.provider or "vertex_gemini";intent.model=response.model;intent.latency_ms=response.latency_ms
            await self._audit("llm_extraction_success",allowed=True,intent=intent,latency=response.latency_ms,user=user,conversation_id=conversation_id)
            return intent
        except (json.JSONDecodeError,ValidationError,AppError,Exception) as exc:
            await self._audit("llm_extraction_failed",allowed=False,output=type(exc).__name__,user=user,conversation_id=conversation_id)
            if settings.extraction_fallback_to_rules:
                await self._audit("llm_extraction_fallback_to_rules",allowed=True,fallback=True,user=user,conversation_id=conversation_id)
                return None
            if isinstance(exc,AppError): raise
            raise AppError("Intent extraction failed.",502) from exc

    @staticmethod
    async def _audit(action: str, allowed: bool, intent: ExtractedIntent | None = None, latency: int | None = None, fallback: bool = False, privacy_blocked: bool = False, output: str | None = None, user: str = "unknown", conversation_id: str | None = None):
        await log_audit_event(AuditEvent(user=user,conversation_id=conversation_id,action=action,allowed=allowed,risk_level="low",agent_name="llm_extraction",intent=intent.intent if intent else None,operation=intent.operation if intent else None,doctype=intent.doctype if intent else None,report_name=intent.report_name if intent else None,output_summary=output,provider=intent.provider if intent else "vertex_gemini",model=intent.model if intent else None,extraction_method=intent.extraction_method if intent else None,confidence=intent.confidence if intent else None,latency_ms=latency,fallback_used=fallback,privacy_blocked=privacy_blocked))
