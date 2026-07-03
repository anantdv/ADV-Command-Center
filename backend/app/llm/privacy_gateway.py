import re
from typing import Any

from pydantic import BaseModel, Field

from app.config import settings


class PrivacyViolationError(ValueError):
    """Raised before an unsafe payload can reach an external model."""

    def __init__(self, categories: list[str]):
        self.categories = list(dict.fromkeys(categories))
        super().__init__("Outbound LLM payload contains restricted ERP or credential data.")


class PrivacyCheckResult(BaseModel):
    allowed: bool
    reason: str | None = None
    redacted_payload: dict[str, Any] | None = None
    detected_categories: list[str] = Field(default_factory=list)


class PrivacyGateway:
    """Allowlist gateway for the one and only Vertex-bound payload shape."""

    ALLOWED_KEYS = {
        "user_message",
        "module_context",
        "current_date",
        "allowed_doctypes",
        "allowed_reports",
        "allowed_file_formats",
        "allowed_widget_types",
        "allowed_operations",
    }
    BLOCKED_KEYS = {
        "records",
        "rows",
        "result",
        "results",
        "data_rows",
        "report_rows",
        "table_data",
        "chart_data",
        "invoice_data",
        "ledger_entries",
        "stock_entries",
        "customers",
        "suppliers",
        "items",
        "sales_invoices",
        "purchase_invoices",
        "payments",
        "payroll",
        "salary",
        "api_key",
        "api_secret",
        "token",
        "sid",
        "cookie",
        "cookies",
        "authorization",
        "password",
    }
    RESTRICTED_TEXT = re.compile(
        r"(?:ACC-SINV-|\bSINV-|\bPINV-|\bGL\s+Entry\b|\bPayment\s+Entry\b|"
        r"\bJournal\s+Entry\b|\bSalary\s+Slip\b|\bAPI\s+Secret\b|"
        r"\bAuthorization\s*:|\bsid\s*=)",
        re.IGNORECASE,
    )
    CREDENTIAL_VALUE = re.compile(
        r"\b(?:api[_ ]?key|api[_ ]?secret|token|sid|password|authorization|cookie)\s*[:=]\s*\S+",
        re.IGNORECASE,
    )

    def check_outbound_payload(self, payload: dict[str, Any]) -> PrivacyCheckResult:
        try:
            assert_safe_for_external_llm(payload)
        except PrivacyViolationError as exc:
            return PrivacyCheckResult(
                allowed=False,
                reason=str(exc),
                detected_categories=exc.categories,
            )

        outbound = dict(payload)
        if settings.llm_redaction_enabled:
            outbound["user_message"] = self.redact_text(str(payload.get("user_message") or ""))
            if outbound.get("module_context") is not None:
                outbound["module_context"] = self.redact_text(str(outbound["module_context"]))
        return PrivacyCheckResult(allowed=True, redacted_payload=outbound)

    @classmethod
    def scan(cls, payload: dict[str, Any]) -> list[str]:
        categories: list[str] = []
        extra = set(payload) - cls.ALLOWED_KEYS
        if extra:
            categories.append("disallowed_payload_keys")

        missing = cls.ALLOWED_KEYS - set(payload)
        if missing:
            categories.append("missing_allowlisted_keys")

        cls._scan_value(payload, categories)
        prompt = str(payload.get("user_message") or "")
        if not prompt.strip():
            categories.append("empty_prompt")
        if len(prompt) > 8000:
            categories.append("oversized_prompt")

        for key in (
            "allowed_doctypes",
            "allowed_reports",
            "allowed_file_formats",
            "allowed_widget_types",
            "allowed_operations",
        ):
            value = payload.get(key)
            if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
                categories.append("invalid_allowed_vocabulary")

        module_context = payload.get("module_context")
        if module_context is not None and not isinstance(module_context, str):
            categories.append("invalid_module_context")
        return list(dict.fromkeys(categories))

    @classmethod
    def _scan_value(cls, value: Any, categories: list[str]) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).strip().lower() in cls.BLOCKED_KEYS:
                    categories.append("erp_or_secret_key")
                cls._scan_value(item, categories)
        elif isinstance(value, list):
            for item in value:
                cls._scan_value(item, categories)
        elif isinstance(value, str):
            if cls.RESTRICTED_TEXT.search(value):
                categories.append("restricted_erp_pattern")
            if cls.CREDENTIAL_VALUE.search(value):
                categories.append("credential_value")

    @classmethod
    def redact_text(cls, text: str) -> str:
        return cls.CREDENTIAL_VALUE.sub("[REDACTED]", text)[:8000]


def assert_safe_for_external_llm(payload: dict[str, Any]) -> None:
    """Raise before provider invocation unless the payload is minimal and safe."""
    if not isinstance(payload, dict):
        raise PrivacyViolationError(["invalid_payload_type"])
    categories = PrivacyGateway.scan(payload)
    if categories:
        raise PrivacyViolationError(categories)


RAG_ALLOWED_KEYS = {"question", "approved_context", "citation_ids", "source_titles"}
RAG_CONTEXT_KEYS = {"citation_id", "source_id", "source_type", "title", "content"}
RAG_BLOCKED_KEYS = PrivacyGateway.BLOCKED_KEYS | {
    "grand_total", "outstanding_amount", "valuation_rate", "debit", "credit",
    "customer", "supplier", "item_code", "employee", "account_no",
}
RAG_RESTRICTED_TEXT = re.compile(
    r"(?:ACC-SINV-|\bSINV-|\bPINV-|\bSAL-ORD-|\bPUR-ORD-|"
    r"\bSalary\s+Slip\b|\bpayroll\b|\bAPI\s+Secret\b|"
    r"\bAuthorization\s*:|\bsid\s*=)",
    re.IGNORECASE,
)


def assert_safe_knowledge_content(content: str) -> None:
    """Reject credentials and record-like ERP data before indexing."""
    categories: list[str] = []
    if PrivacyGateway.CREDENTIAL_VALUE.search(content):
        categories.append("credential_value")
    if RAG_RESTRICTED_TEXT.search(content):
        categories.append("transaction_or_sensitive_pattern")
    if len(re.findall(r"\b(?:CUST|SUPP|ITEM)-[A-Z0-9-]+\b", content, re.I)) >= 3:
        categories.append("master_record_list")
    if categories:
        raise PrivacyViolationError(categories)


def assert_safe_rag_payload(payload: dict[str, Any]) -> None:
    """Validate the separate approved-knowledge payload sent for RAG."""
    if not isinstance(payload, dict) or set(payload) != RAG_ALLOWED_KEYS:
        raise PrivacyViolationError(["invalid_rag_payload_shape"])
    contexts = payload.get("approved_context")
    if not isinstance(contexts, list):
        raise PrivacyViolationError(["invalid_rag_context"])
    categories: list[str] = []
    for context in contexts:
        if not isinstance(context, dict) or set(context) != RAG_CONTEXT_KEYS:
            categories.append("invalid_rag_context")
            continue
        lowered = {str(key).lower() for key in context}
        if lowered & RAG_BLOCKED_KEYS:
            categories.append("erp_record_fields")
        try:
            assert_safe_knowledge_content(str(context.get("content") or ""))
        except PrivacyViolationError as exc:
            categories.extend(exc.categories)
    question = str(payload.get("question") or "")
    if PrivacyGateway.CREDENTIAL_VALUE.search(question):
        categories.append("credential_value")
    if categories:
        raise PrivacyViolationError(categories)
