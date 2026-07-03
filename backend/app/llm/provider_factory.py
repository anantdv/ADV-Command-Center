from app.config import settings
from app.core.exceptions import AppError
from app.llm.base import BaseLLMProvider
from app.llm.vertex_gemini_provider import VertexGeminiProvider


def get_llm_provider() -> BaseLLMProvider | None:
    if not settings.enable_llm_extraction or settings.llm_provider == "disabled": return None
    settings.validate_llm_runtime()
    if not settings.llm_allow_external: return None
    if settings.llm_allow_erp_data or settings.llm_allow_master_data or settings.llm_allow_transaction_data or settings.llm_allow_report_rows:
        raise AppError("ERP data sharing with external models is not supported.", 500)
    if settings.llm_provider != "vertex_gemini": raise AppError(f"Unsupported LLM provider: {settings.llm_provider}", 500)
    if not settings.google_cloud_project: raise AppError("GOOGLE_CLOUD_PROJECT is required for Vertex Gemini.", 500)
    return VertexGeminiProvider(settings.google_cloud_project,settings.google_cloud_location,settings.vertex_gemini_model,settings.llm_timeout_seconds,settings.llm_temperature,settings.llm_max_output_tokens)
