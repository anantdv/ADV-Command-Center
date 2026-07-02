import json
import re
from typing import Any

from pydantic import BaseModel, Field

from app.config import settings


class PrivacyCheckResult(BaseModel):
    allowed: bool
    reason: str | None = None
    redacted_payload: dict[str, Any] | None = None
    detected_categories: list[str] = Field(default_factory=list)


class PrivacyGateway:
    ALLOWED_KEYS = {"user_message", "module_context", "current_date", "allowed_doctypes", "allowed_reports", "allowed_file_formats", "allowed_widget_types"}
    ROW_KEYS = {"records", "rows", "result", "data_rows", "report_rows", "query_result", "report_output"}
    SECRET_KEYS = {"api_key", "api_secret", "sid", "session_id", "cookie", "cookies", "token", "password", "authorization"}
    BUSINESS_ROW_FIELDS = {"customer_name", "supplier_name", "grand_total", "outstanding_amount", "posting_date", "valuation_rate", "salary"}

    def check_outbound_payload(self, payload: dict[str, Any]) -> PrivacyCheckResult:
        categories: list[str] = []
        extra = set(payload) - self.ALLOWED_KEYS
        if extra: categories.append("disallowed_payload_keys")
        self._scan(payload, categories, in_array=False)
        prompt = str(payload.get("user_message") or "")
        if len(prompt) > 8000: categories.append("oversized_prompt")
        if len(re.findall(r"\b(?:ACC-SINV|SINV|PINV|GL[- ]?ENTRY|SAL-ORD|PUR-ORD)-[A-Z0-9-]+\b", prompt, re.I)) >= 3:
            categories.append("record_identifier_list")
        if re.search(r"\b(?:api[_ ]?key|api[_ ]?secret|token|sid|password)\s*[:=]\s*\S+", prompt, re.I):
            categories.append("credential_value")
        categories = list(dict.fromkeys(categories))
        if categories:
            return PrivacyCheckResult(allowed=False, reason="Outbound LLM payload contains restricted ERP or credential data.", detected_categories=categories)
        redacted = dict(payload)
        if settings.llm_redaction_enabled:
            redacted["user_message"] = self.redact_text(prompt)
        return PrivacyCheckResult(allowed=True, redacted_payload=redacted)

    def _scan(self, value: Any, categories: list[str], in_array: bool) -> None:
        if isinstance(value, dict):
            lowered = {str(key).lower() for key in value}
            if lowered & self.ROW_KEYS: categories.append("erp_rows")
            if lowered & self.SECRET_KEYS: categories.append("credentials")
            if in_array and len(lowered & self.BUSINESS_ROW_FIELDS) >= 2: categories.append("business_record_array")
            for item in value.values(): self._scan(item, categories, in_array=False)
        elif isinstance(value, list):
            if len(value) > 100 and any(isinstance(item, dict) for item in value): categories.append("large_tabular_payload")
            for item in value: self._scan(item, categories, in_array=True)

    @staticmethod
    def redact_text(text: str) -> str:
        redacted = re.sub(r"(?i)\b(api[_ ]?key|api[_ ]?secret|token|sid|password)\s*[:=]\s*\S+", r"\1=[REDACTED]", text)
        return redacted[:8000]

