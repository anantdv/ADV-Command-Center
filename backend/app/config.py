from functools import lru_cache
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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
