from app.utils.ocr_layout_extractor import OcrTextBlock


def test_ocr_text_block_serializes_layout_fields():
    block = OcrTextBlock(text="Invoice", page=1, x=10, y=20, width=50, height=12, confidence=91)

    assert block.to_dict()["text"] == "Invoice"
    assert block.to_dict()["confidence"] == 91
