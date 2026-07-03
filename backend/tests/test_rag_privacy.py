import pytest

from app.llm.privacy_gateway import PrivacyViolationError, assert_safe_knowledge_content, assert_safe_rag_payload


def safe_payload(content="Open the document and verify your permissions before clicking Submit."):
    return {"question":"How do I submit?","approved_context":[{"citation_id":"C1","source_id":"src_1","source_type":"sop_document","title":"Submission SOP","content":content}],"citation_ids":["C1"],"source_titles":["Submission SOP"]}


def test_rag_allows_approved_procedure_content():
    assert_safe_rag_payload(safe_payload())


@pytest.mark.parametrize("content",["Invoice ACC-SINV-2026-00001 belongs to ABC","Payroll instructions include Salary Slip values","Authorization: Bearer secret","sid=secret"])
def test_rag_blocks_transaction_and_secret_patterns(content):
    with pytest.raises(PrivacyViolationError): assert_safe_rag_payload(safe_payload(content))


def test_rag_rejects_row_shaped_context():
    payload=safe_payload();payload["approved_context"][0]["rows"]=[{"customer":"ABC","grand_total":1000}]
    with pytest.raises(PrivacyViolationError): assert_safe_rag_payload(payload)


def test_indexing_rejects_master_record_lists():
    with pytest.raises(PrivacyViolationError): assert_safe_knowledge_content("CUST-001 CUST-002 CUST-003")
