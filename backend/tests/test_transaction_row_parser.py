from app.utils.payload_builder import PayloadBuilder
from app.utils.transaction_row_parser import transaction_row_parser


def test_transaction_row_parser_removes_qty_and_price_from_item_query():
    rows = transaction_row_parser.parse_many("tcl top mount fridge qty 1 price 1500")

    assert rows == [
        {
            "source_text": "tcl top mount fridge qty 1 price 1500",
            "qty": 1,
            "rate": 1500,
            "rate_source": "user",
            "item_query": "tcl top mount fridge",
            "amount": 1500.0,
            "raw_query": "tcl top mount fridge",
            "normalized_query": "tcl top mount fridge",
            "description": "tcl top mount fridge",
        }
    ]


def test_transaction_row_parser_supports_common_rate_syntaxes():
    cases = [
        ("TV qty 2 price 1500", "TV", 2, 1500),
        ("2 TVs at 1500 each", "TVs", 2, 1500),
        ("oven x 3 @ 250", "oven", 3, 250),
        ("10 rice bags rate 8", "rice bags", 10, 8),
        ("air fryer quantity 2 unit price 350", "air fryer", 2, 350),
    ]

    for text, query, qty, rate in cases:
        row = transaction_row_parser.parse_many(text)[0]
        assert row["item_query"] == query
        assert row["qty"] == qty
        assert row["rate"] == rate
        assert row["rate_source"] == "user"
        assert "qty" not in row["item_query"].lower()
        assert "price" not in row["item_query"].lower()


def test_payload_builder_does_not_treat_document_header_as_item_row():
    payload = PayloadBuilder.extract_create("Purchase Order", "create po for bnbm")

    assert payload == {"supplier": "bnbm"}


def test_sales_invoice_payload_preserves_clean_item_row_and_rate():
    payload = PayloadBuilder.extract_create(
        "Sales Invoice",
        "create a sales invoice for biswajit for item tcl top mount fridge qty 1 price 1500",
    )

    assert payload["customer"] == "biswajit"
    assert payload["items"][0]["item_query"] == "tcl top mount fridge"
    assert payload["items"][0]["qty"] == 1
    assert payload["items"][0]["rate"] == 1500
    assert payload["items"][0]["rate_source"] == "user"
