import pytest

from app.utils.date_range_parser import parse_date_range_phrase
from app.utils.filter_normalizer import FilterNormalizationError, normalize_filters


def test_may_2025_date_range():
    assert parse_date_range_phrase("may 2025") == {"from_date": "2025-05-01", "to_date": "2025-05-31"}


def test_january_to_march_2025_date_range():
    assert parse_date_range_phrase("from january 2025 to march 2025") == {"from_date": "2025-01-01", "to_date": "2025-03-31"}


def test_unpaid_sales_invoice_with_date_range():
    assert normalize_filters("Sales Invoice", {"status": "unpaid"}, {"from_date": "2025-05-01", "to_date": "2025-05-31"}) == {
        "status": ["in", ["Unpaid", "Overdue"]],
        "posting_date": ["between", ["2025-05-01", "2025-05-31"]],
    }


def test_purchase_order_value_between_alias():
    assert normalize_filters("Purchase Order", {"value": {"between": [40000, 50000]}}) == {
        "grand_total": ["between", [40000, 50000]]
    }


def test_above_value_operator_object():
    assert normalize_filters("Sales Invoice", {"amount": {"operator": ">", "value": 50000}}) == {
        "grand_total": [">", 50000]
    }


def test_below_value_operator_object():
    assert normalize_filters("Purchase Invoice", {"total": {"operator": "<", "value": 10000}}) == {
        "grand_total": ["<", 10000]
    }


def test_date_from_to_object():
    assert normalize_filters("Sales Invoice", {"posting_date": {"from": "2025-05-01", "to": "2025-05-31"}}) == {
        "posting_date": ["between", ["2025-05-01", "2025-05-31"]]
    }


def test_invalid_operator_raises():
    with pytest.raises(FilterNormalizationError):
        normalize_filters("Sales Invoice", {"grand_total": ["drop table", 1000]})
