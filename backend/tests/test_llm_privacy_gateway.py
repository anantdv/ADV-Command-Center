import pytest

from app.llm.privacy_gateway import PrivacyGateway, PrivacyViolationError, assert_safe_for_external_llm


def safe_payload(**overrides):
    payload={"user_message":"show customers","module_context":"Selling","current_date":"2026-07-02","allowed_doctypes":["Customer"],"allowed_reports":[],"allowed_file_formats":["pdf"],"allowed_widget_types":["table"],"allowed_operations":["read"]}
    return {**payload, **overrides}


def test_allows_only_minimal_intent_payload():
    result=PrivacyGateway().check_outbound_payload(safe_payload())
    assert result.allowed is True


def test_blocks_records_and_report_rows():
    gateway=PrivacyGateway()
    for payload in (safe_payload(records=[{"customer_name":"A"}]),safe_payload(report_rows=[{"grand_total":100}])):
        result=gateway.check_outbound_payload(payload)
        assert result.allowed is False
        assert result.detected_categories


def test_blocks_nested_rows_and_credentials():
    gateway=PrivacyGateway()
    rows=gateway.check_outbound_payload(safe_payload(module_context="Selling", chart_data=[{"customer_name":"A","grand_total":100}]))
    assert rows.allowed is False
    assert "erp_or_secret_key" in rows.detected_categories
    secret=gateway.check_outbound_payload(safe_payload(user_message="use token=secret-value"))
    assert secret.allowed is False
    assert "credential_value" in secret.detected_categories


def test_redaction_never_preserves_credential_values():
    assert "secret-value" not in PrivacyGateway.redact_text("api_key=secret-value")


@pytest.mark.parametrize("text", ["show ACC-SINV-2026-00001", "GL Entry", "Authorization: Bearer x", "sid=abc"])
def test_blocks_restricted_erp_and_auth_patterns(text):
    result=PrivacyGateway().check_outbound_payload(safe_payload(user_message=text))
    assert result.allowed is False


def test_assert_safe_raises_before_provider_use():
    with pytest.raises(PrivacyViolationError):
        assert_safe_for_external_llm(safe_payload(results=[{"name":"CUST-001"}]))
