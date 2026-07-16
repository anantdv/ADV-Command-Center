from app.utils.ocr_party_matcher import extract_likely_supplier_names_from_header


def test_supplier_invoice_uses_header_not_sold_to():
    text = """
    PAPUA NIUGINI FREEZERS
    A Division of BAG Wang Company
    Tax Invoice
    Invoice No: INV-1001
    Sold To:
    Courts PNG Limited
    """
    candidates = extract_likely_supplier_names_from_header(text)
    assert candidates
    assert candidates[0]["candidate_name"] == "PAPUA NIUGINI FREEZERS"
    assert "Courts" not in candidates[0]["candidate_name"]
