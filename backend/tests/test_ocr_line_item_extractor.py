from app.utils.amount_parser import parse_amount
from app.utils.ocr_line_item_extractor import extract_line_items_from_text


def test_amount_parser_supports_currency_and_commas():
    assert parse_amount("PGK 1,234.50") == 1234.50
    assert parse_amount("$1,234.50") == 1234.50


def test_simple_invoice_line_table_is_extracted():
    text = """
    Description Qty Rate Amount
    ITEM-001 Laptop 2 1500.00 3000.00
    Laptop Bag 5 25.00 125.00
    Grand Total 3125.00
    """
    items = extract_line_items_from_text(text)
    assert len(items) == 2
    assert items[0].item_code == "ITEM-001"
    assert items[0].qty == 2
    assert items[0].amount == 3000
