from app.utils.date_parser import parse_any_date
from app.utils.ocr_field_extractor import extract_document_fields, is_label_like


def test_labels_are_not_extracted_as_bill_values():
    text = """
    Supplier Invoice
    Invoice No
    Fax
    Bill Date
    Invoice No
    Supplier: Pacific Hardware Ltd
    """
    fields = extract_document_fields(text)
    assert fields.bill_no is None
    assert fields.bill_date is None
    assert is_label_like("Fax")
    assert is_label_like("Invoice No")


def test_valid_invoice_number_and_date_are_extracted():
    fields = extract_document_fields("Tax Invoice\nInvoice No: INV-1001\nInvoice Date: 16/07/2026\nSupplier: Pacific Hardware Ltd")
    assert fields.bill_no == "INV-1001"
    assert fields.bill_date == "2026-07-16"


def test_date_parser_supports_common_formats():
    assert parse_any_date("16/07/2026") == "2026-07-16"
    assert parse_any_date("16-Jul-2026") == "2026-07-16"
    assert parse_any_date("Jul 16, 2026") == "2026-07-16"
