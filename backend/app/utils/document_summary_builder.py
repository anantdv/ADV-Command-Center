from __future__ import annotations

from typing import Any

SUMMARY_FIELDS = ("name", "title", "workflow_state", "status", "posting_date", "transaction_date", "customer", "supplier", "party_name", "grand_total", "currency")
SENSITIVE_PARTS = ("password", "secret", "token", "api_key", "api_secret", "salary", "bank", "account_no", "pan", "aadhaar")


def build_document_summary(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if key in SUMMARY_FIELDS and not any(part in key.lower() for part in SENSITIVE_PARTS)}
