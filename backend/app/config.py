from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Environment-backed application settings."""

    app_name: str = "ADV Command Center"
    app_env: str = "development"
    api_prefix: str = "/api"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:5173", "http://localhost:3000"]
    database_url: str = "sqlite:///./erp_ai_command_center.db"
    frappe_base_url: str = "http://localhost:8000"
    frappe_auth_mode: str = "session"
    frappe_api_key: str | None = None
    frappe_api_secret: str | None = None
    frappe_forward_session_cookie: bool = True
    frappe_session_cookie_name: str = "sid"
    use_mock_data: bool = True
    enable_ai_runtime: bool = False
    enable_external_model: bool = False
    local_model_base_url: str = "http://localhost:11434"
    local_model_name: str = "llama3.1"
    secret_key: str = "change-me"
    file_storage_backend: str = "local"
    file_storage_root: str = "./generated_files"
    file_download_base_url: str = "http://localhost:8000/api/library/files"
    max_export_rows: int = 5000
    pdf_renderer: str = "reportlab"
    enable_file_generation: bool = True
    enable_llm_extraction: bool = False
    llm_provider: str = "disabled"
    llm_mode: str = "intent_only"
    google_cloud_project: str | None = None
    google_cloud_location: str = "us-central1"
    vertex_gemini_model: str = "gemini-2.5-flash"
    google_application_credentials: str | None = None
    llm_allow_external: bool = False
    llm_allow_erp_data: bool = False
    llm_allow_master_data: bool = False
    llm_allow_transaction_data: bool = False
    llm_allow_report_rows: bool = False
    llm_redaction_enabled: bool = True
    llm_fail_closed: bool = True
    llm_log_prompts: bool = False
    llm_log_responses: bool = False
    llm_log_redacted_prompts: bool = False
    llm_timeout_seconds: int = 30
    llm_max_output_tokens: int = 1200
    llm_temperature: float = 0.0
    llm_confidence_threshold: float = 0.65
    extraction_fallback_to_rules: bool = True
    allow_unsafe_llm_config: bool = False
    enable_knowledge_base: bool = True
    enable_rag: bool = True
    knowledge_storage_root: str = "./knowledge_files"
    knowledge_vector_backend: str = "numpy"
    knowledge_chunk_size: int = 900
    knowledge_chunk_overlap: int = 150
    knowledge_top_k: int = 5
    knowledge_max_file_bytes: int = 20 * 1024 * 1024
    embedding_provider: str = "vertex"
    vertex_embedding_model: str = "text-embedding-005"
    rag_llm_provider: str = "vertex_gemini"
    rag_gemini_model: str = "gemini-2.5-flash"
    rag_max_context_chunks: int = 5
    rag_require_citations: bool = True
    rag_allow_erp_data: bool = False
    rag_allow_transaction_data: bool = False
    rag_allow_master_data: bool = False
    rag_fail_closed: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("frappe_auth_mode")
    @classmethod
    def validate_frappe_auth_mode(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized not in {"token", "session"}:
            raise ValueError("FRAPPE_AUTH_MODE must be 'token' or 'session'")
        return normalized

    @field_validator("file_storage_backend")
    @classmethod
    def validate_file_storage_backend(cls, value: str) -> str:
        normalized = value.strip().lower()
        if normalized != "local":
            raise ValueError("Only FILE_STORAGE_BACKEND=local is supported in this release")
        return normalized

    @field_validator("max_export_rows")
    @classmethod
    def validate_max_export_rows(cls, value: int) -> int:
        return min(max(value, 1), 50_000)

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, value: str) -> str:
        normalized=value.strip().lower()
        if normalized not in {"disabled","vertex_gemini"}: raise ValueError("LLM_PROVIDER must be disabled or vertex_gemini")
        return normalized

    @field_validator("llm_mode")
    @classmethod
    def validate_llm_mode(cls, value: str) -> str:
        if value.strip().lower() != "intent_only": raise ValueError("Only LLM_MODE=intent_only is supported")
        return "intent_only"

    @field_validator("llm_confidence_threshold")
    @classmethod
    def validate_confidence(cls, value: float) -> float: return min(max(value,0),1)

    def validate_llm_runtime(self) -> None:
        """Fail startup when an enabled external LLM could receive ERP data.

        The development override exists only for local diagnostics. Production
        can never opt out of these checks.
        """
        if not self.enable_llm_extraction:
            return

        errors: list[str] = []
        if self.llm_provider != "vertex_gemini":
            errors.append("LLM_PROVIDER must be vertex_gemini")
        if self.llm_mode != "intent_only":
            errors.append("LLM_MODE must be intent_only")
        if not self.google_cloud_project:
            errors.append("GOOGLE_CLOUD_PROJECT is required")
        if not self.google_cloud_location:
            errors.append("GOOGLE_CLOUD_LOCATION is required")
        if not self.vertex_gemini_model:
            errors.append("VERTEX_GEMINI_MODEL is required")
        if not self.google_application_credentials:
            errors.append("GOOGLE_APPLICATION_CREDENTIALS is required")
        elif not Path(self.google_application_credentials).expanduser().is_file():
            errors.append("GOOGLE_APPLICATION_CREDENTIALS file does not exist")
        if not self.llm_allow_external:
            errors.append("LLM_ALLOW_EXTERNAL must be true")
        if self.llm_allow_erp_data:
            errors.append("LLM_ALLOW_ERP_DATA must be false")
        if self.llm_allow_master_data:
            errors.append("LLM_ALLOW_MASTER_DATA must be false")
        if self.llm_allow_transaction_data:
            errors.append("LLM_ALLOW_TRANSACTION_DATA must be false")
        if self.llm_allow_report_rows:
            errors.append("LLM_ALLOW_REPORT_ROWS must be false")
        if not self.llm_fail_closed:
            errors.append("LLM_FAIL_CLOSED must be true")

        unsafe_override = self.app_env == "development" and self.allow_unsafe_llm_config
        if errors and not unsafe_override:
            raise RuntimeError("Unsafe Vertex Gemini configuration: " + "; ".join(errors))

    def validate_rag_runtime(self) -> None:
        if not self.enable_rag:
            return
        errors: list[str] = []
        if not self.enable_knowledge_base:
            errors.append("ENABLE_KNOWLEDGE_BASE must be true")
        if self.knowledge_vector_backend != "numpy":
            errors.append("KNOWLEDGE_VECTOR_BACKEND must be numpy")
        if self.embedding_provider != "vertex" and not self.use_mock_data:
            errors.append("EMBEDDING_PROVIDER must be vertex")
        if self.rag_llm_provider != "vertex_gemini" and not self.use_mock_data:
            errors.append("RAG_LLM_PROVIDER must be vertex_gemini")
        if self.rag_allow_erp_data or self.rag_allow_transaction_data or self.rag_allow_master_data:
            errors.append("all RAG ERP/master/transaction sharing flags must be false")
        if not self.rag_fail_closed:
            errors.append("RAG_FAIL_CLOSED must be true")
        if not self.use_mock_data:
            if not self.google_cloud_project:
                errors.append("GOOGLE_CLOUD_PROJECT is required for RAG")
            if not self.google_cloud_location:
                errors.append("GOOGLE_CLOUD_LOCATION is required for RAG")
            if not self.vertex_embedding_model:
                errors.append("VERTEX_EMBEDDING_MODEL is required")
            if not self.rag_gemini_model:
                errors.append("RAG_GEMINI_MODEL is required")
            if not self.google_application_credentials:
                errors.append("GOOGLE_APPLICATION_CREDENTIALS is required for RAG")
            elif not Path(self.google_application_credentials).expanduser().is_file():
                errors.append("GOOGLE_APPLICATION_CREDENTIALS file does not exist for RAG")
        unsafe_override = self.app_env == "development" and self.allow_unsafe_llm_config
        if errors and not unsafe_override:
            raise RuntimeError("Unsafe RAG configuration: " + "; ".join(errors))


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
