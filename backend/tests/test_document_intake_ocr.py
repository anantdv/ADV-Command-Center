def test_document_classifier_supplier_invoice():
    from app.utils.document_classifier import classify_document_type
    assert classify_document_type("Tax Invoice\nSupplier: Pacific Hardware\nInvoice No: INV-1001") == "supplier_invoice"


def test_ocr_field_extractor_maps_supplier_invoice():
    from app.utils.ocr_field_extractor import extract_document_fields
    fields = extract_document_fields("Tax Invoice\nSupplier: Pacific Hardware\nInvoice No: INV-1001\nGrand Total 5,000")
    assert fields.target_doctype == "Purchase Invoice"
    assert fields.supplier == "Pacific Hardware"
    assert fields.bill_no == "INV-1001"


def test_upload_rejects_path_traversal_intake(client):
    response = client.get("/api/document-intake/../bad")
    assert response.status_code in {404, 405}
