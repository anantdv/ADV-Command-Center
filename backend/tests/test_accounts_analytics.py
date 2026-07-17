from app.utils.analytics_catalog import ANALYTICS_CATALOG


def test_accounts_catalog_includes_receivables_and_payables():
    assert ANALYTICS_CATALOG["receivables_aging"]["source_name"] == "Accounts Receivable"
    assert ANALYTICS_CATALOG["payables_aging"]["source_name"] == "Accounts Payable"


def test_monthly_sales_vs_purchase_is_whitelisted_composite():
    definition = ANALYTICS_CATALOG["monthly_sales_vs_purchase"]

    assert definition["source_type"] == "composite"
    assert definition["source_name"] == "Sales Invoice + Purchase Invoice"
