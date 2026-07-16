from app.utils.pdf_text_extractor import ExtractedDocumentText, is_good_pdf_text


def test_good_pdf_text_requires_length_and_invoice_keyword():
    document = ExtractedDocumentText(
        source="pdf_text",
        full_text=("Tax Invoice\nInvoice No: INV-1001\nGrand Total 100.00\n" * 5),
        pages=[],
        confidence=0.8,
        diagnostics={"invoice_like_keywords": ["invoice", "total"]},
    )

    assert is_good_pdf_text(document)


def test_weak_pdf_text_is_not_good():
    document = ExtractedDocumentText(source="pdf_text", full_text="hello", pages=[], confidence=0.1, diagnostics={"invoice_like_keywords": []})

    assert not is_good_pdf_text(document)
