import asyncio
import json
import time

from app.core.exceptions import AppError
from app.llm.base import BaseLLMProvider, LLMMessage, LLMResponse


class VertexGeminiProvider(BaseLLMProvider):
    """Lazy Vertex SDK adapter with a mandatory purpose-specific privacy check."""
    def __init__(self, project_id: str, location: str, model_name: str, timeout_seconds: int = 30, temperature: float = 0.0, max_output_tokens: int = 1200):
        self.project_id=project_id;self.location=location;self.model_name=model_name;self.timeout_seconds=timeout_seconds;self.temperature=temperature;self.max_output_tokens=max_output_tokens

    async def complete(self, messages: list[LLMMessage], response_schema: dict | None = None, **kwargs) -> LLMResponse:
        started=time.perf_counter()
        purpose=str(kwargs.get("purpose") or "intent_extraction")
        try:
            content = await asyncio.wait_for(asyncio.to_thread(self._complete_sync, messages, response_schema, purpose), timeout=self.timeout_seconds)
        except asyncio.TimeoutError as exc: raise AppError("Vertex Gemini intent extraction timed out.", 504) from exc
        except AppError: raise
        except Exception as exc: raise AppError("Vertex Gemini intent extraction is unavailable.", 502, {"provider":"vertex_gemini"}) from exc
        return LLMResponse(content=content, model=self.model_name, provider="vertex_gemini", latency_ms=round((time.perf_counter()-started)*1000))

    def _complete_sync(self, messages: list[LLMMessage], response_schema: dict | None, purpose: str) -> str:
        try:
            from google import genai
            from google.genai import types
        except ImportError as exc: raise AppError("google-genai is not installed.", 503) from exc
        system = "\n".join(message.content for message in messages if message.role == "system")
        user = "\n".join(message.content for message in messages if message.role != "system")
        try:
            outbound=json.loads(user)
        except json.JSONDecodeError as exc:
            raise AppError("Vertex outbound payload must be validated JSON.",500) from exc
        if purpose in {"approved_knowledge_rag","training_assessment"}:
            from app.llm.privacy_gateway import assert_safe_rag_payload
            assert_safe_rag_payload(outbound)
        else:
            from app.llm.privacy_gateway import assert_safe_for_external_llm
            assert_safe_for_external_llm(outbound)
        client=genai.Client(vertexai=True,project=self.project_id,location=self.location)
        config_args={"system_instruction":system,"temperature":self.temperature,"max_output_tokens":self.max_output_tokens,"response_mime_type":"application/json"}
        if response_schema: config_args["response_schema"]=response_schema
        try:
            response=client.models.generate_content(model=self.model_name,contents=user,config=types.GenerateContentConfig(**config_args))
        except (TypeError, ValueError):
            # Keep JSON-only prompting as a compatibility fallback when a
            # regional model version rejects the supplied response schema.
            config_args.pop("response_schema",None)
            response=client.models.generate_content(model=self.model_name,contents=user,config=types.GenerateContentConfig(**config_args))
        return str(response.text or "")
