from app.utils.ocr_field_extractor import extract_document_fields, extract_field_candidates
from app.utils.ocr_party_matcher import extract_likely_supplier_names_from_header


def test_bill_no_same_line_and_date_not_defaulted():
    lines = [
        "PAPUA NIUGINI FREEZERS",
        "Tax Invoice",
        "Invoice No: INV-12345",
        "Invoice Date: 15/07/2026",
        "Description Qty Rate Amount",
        "Frozen Chicken 2 50.00 100.00",
        "Grand Total 100.00",
    ]

    fields = extract_document_fields("\n".join(lines), lines=lines)

    assert fields.bill_no == "INV-12345"
    assert fields.bill_date == "2026-07-15"
    assert fields.posting_date
    assert fields.items


def test_bill_date_stays_blank_when_only_label_exists():
    fields = extract_document_fields("Tax Invoice\nInvoice No\nFax\nBill Date\nGrand Total 100.00", lines=["Tax Invoice", "Invoice No", "Fax", "Bill Date", "Grand Total 100.00"])

    assert fields.bill_date is None


def test_supplier_header_candidate_detects_png_freezers_before_sold_to():
    candidates = extract_likely_supplier_names_from_header(
        "PAPUA NIUGINI FREEZERS A Division of BAG Wang Company Canitet Sold To: ABC Customer\nInvoice No: INV-1"
    )

    assert candidates
    assert candidates[0]["candidate_name"] == "PAPUA NIUGINI FREEZERS"


def test_field_candidates_reject_label_values():
    candidates = extract_field_candidates(["Invoice No", "Fax", "Bill Date", "Date"])

    assert candidates["bill_no"] == []
    assert candidates["bill_date"] == []
