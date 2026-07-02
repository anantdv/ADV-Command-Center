from app.llm.privacy_gateway import PrivacyGateway


def test_allows_only_minimal_intent_payload():
    result=PrivacyGateway().check_outbound_payload({"user_message":"show customers","module_context":"Selling","current_date":"2026-07-02","allowed_doctypes":["Customer"],"allowed_reports":[],"allowed_file_formats":["pdf"],"allowed_widget_types":["table"]})
    assert result.allowed is True


def test_blocks_records_and_report_rows():
    gateway=PrivacyGateway()
    for payload in ({"user_message":"show customers","records":[{"customer_name":"A"}]},{"user_message":"report","report_rows":[{"grand_total":100}]}):
        result=gateway.check_outbound_payload(payload)
        assert result.allowed is False
        assert result.detected_categories


def test_blocks_business_record_arrays_and_credentials():
    gateway=PrivacyGateway()
    rows=gateway.check_outbound_payload({"user_message":"x","module_context":[{"customer_name":"A","grand_total":100}],"current_date":"2026-07-02","allowed_doctypes":[],"allowed_reports":[],"allowed_file_formats":[],"allowed_widget_types":[]})
    assert rows.allowed is False
    assert "business_record_array" in rows.detected_categories
    secret=gateway.check_outbound_payload({"user_message":"use token=secret-value","module_context":None,"current_date":"2026-07-02","allowed_doctypes":[],"allowed_reports":[],"allowed_file_formats":[],"allowed_widget_types":[]})
    assert secret.allowed is False
    assert "credential_value" in secret.detected_categories


def test_redaction_never_preserves_credential_values():
    assert "secret-value" not in PrivacyGateway.redact_text("api_key=secret-value")

