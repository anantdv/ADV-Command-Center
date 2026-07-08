FIELD_ALIASES = {
    "Sales Invoice": {
        "invoice_date": "posting_date",
        "date": "posting_date",
        "month": "posting_date",
        "value": "grand_total",
        "amount": "grand_total",
        "total": "grand_total",
        "unpaid_amount": "outstanding_amount",
        "balance": "outstanding_amount",
    },
    "Purchase Invoice": {
        "invoice_date": "posting_date",
        "date": "posting_date",
        "month": "posting_date",
        "value": "grand_total",
        "amount": "grand_total",
        "total": "grand_total",
        "unpaid_amount": "outstanding_amount",
        "balance": "outstanding_amount",
    },
    "Sales Order": {
        "date": "transaction_date",
        "order_date": "transaction_date",
        "month": "transaction_date",
        "value": "grand_total",
        "amount": "grand_total",
        "total": "grand_total",
    },
    "Purchase Order": {
        "date": "transaction_date",
        "order_date": "transaction_date",
        "month": "transaction_date",
        "value": "grand_total",
        "amount": "grand_total",
        "total": "grand_total",
    },
    "Quotation": {
        "date": "transaction_date",
        "quotation_date": "transaction_date",
        "month": "transaction_date",
        "value": "grand_total",
        "amount": "grand_total",
        "total": "grand_total",
    },
}


def map_field_alias(doctype: str, fieldname: str) -> str:
    return FIELD_ALIASES.get(doctype, {}).get(fieldname, fieldname)
