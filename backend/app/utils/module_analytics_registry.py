from __future__ import annotations

from typing import Any


SELLING_ANALYTICS: dict[str, dict[str, Any]] = {
    "monthly_sales_trend": {"key": "monthly_sales_trend", "title": "Monthly Sales Trend", "module": "Selling", "source_type": "doctype", "source_name": "Sales Invoice", "date_field": "posting_date", "group_by": ["month"], "metrics": [{"field": "grand_total", "function": "sum", "label": "Sales"}], "default_chart": "line", "required_fields": ["posting_date", "grand_total"], "drilldown_doctype": "Sales Invoice"},
    "top_customers_by_sales": {"key": "top_customers_by_sales", "title": "Top Customers by Sales", "module": "Selling", "source_type": "doctype", "source_name": "Sales Invoice", "group_by": ["customer"], "metrics": [{"field": "grand_total", "function": "sum", "label": "Sales"}], "default_chart": "bar", "required_fields": ["customer", "grand_total"], "drilldown_doctype": "Sales Invoice"},
    "top_customers_by_outstanding": {"key": "top_customers_by_outstanding", "title": "Top Customers by Outstanding", "module": "Selling", "source_type": "doctype", "source_name": "Sales Invoice", "group_by": ["customer"], "metrics": [{"field": "outstanding_amount", "function": "sum", "label": "Outstanding"}], "default_chart": "bar", "required_fields": ["customer", "outstanding_amount"], "drilldown_doctype": "Sales Invoice"},
    "sales_orders_by_status": {"key": "sales_orders_by_status", "title": "Sales Orders by Status", "module": "Selling", "source_type": "doctype", "source_name": "Sales Order", "group_by": ["status"], "metrics": [{"field": "name", "function": "count", "label": "Count"}], "default_chart": "pie", "required_fields": ["status", "name"], "drilldown_doctype": "Sales Order"},
    "quotation_value_by_month": {"key": "quotation_value_by_month", "title": "Quotation Value by Month", "module": "Selling", "source_type": "doctype", "source_name": "Quotation", "date_field": "transaction_date", "group_by": ["month"], "metrics": [{"field": "grand_total", "function": "sum", "label": "Quotation Value"}], "default_chart": "line", "required_fields": ["transaction_date", "grand_total"], "drilldown_doctype": "Quotation"},
}

BUYING_ANALYTICS: dict[str, dict[str, Any]] = {
    "purchase_trend": {"key": "purchase_trend", "title": "Purchase Trend", "module": "Buying", "source_type": "doctype", "source_name": "Purchase Invoice", "date_field": "posting_date", "group_by": ["month"], "metrics": [{"field": "grand_total", "function": "sum", "label": "Purchase Value"}], "default_chart": "line", "required_fields": ["posting_date", "grand_total"], "drilldown_doctype": "Purchase Invoice"},
    "monthly_purchase_trend": {"key": "monthly_purchase_trend", "title": "Monthly Purchase Trend", "module": "Buying", "source_type": "doctype", "source_name": "Purchase Invoice", "date_field": "posting_date", "group_by": ["month"], "metrics": [{"field": "grand_total", "function": "sum", "label": "Purchases"}], "default_chart": "line", "required_fields": ["posting_date", "grand_total"], "drilldown_doctype": "Purchase Invoice"},
    "purchase_orders_by_supplier": {"key": "purchase_orders_by_supplier", "title": "Purchase Orders by Supplier", "module": "Buying", "source_type": "doctype", "source_name": "Purchase Order", "date_field": "transaction_date", "group_by": ["supplier"], "metrics": [{"field": "grand_total", "function": "sum", "label": "PO Value"}, {"field": "name", "function": "count", "label": "PO Count"}], "default_chart": "bar", "required_fields": ["supplier", "grand_total", "name"], "drilldown_doctype": "Purchase Order"},
    "purchase_invoices_by_supplier": {"key": "purchase_invoices_by_supplier", "title": "Purchase Invoices by Supplier", "module": "Buying", "source_type": "doctype", "source_name": "Purchase Invoice", "date_field": "posting_date", "group_by": ["supplier"], "metrics": [{"field": "grand_total", "function": "sum", "label": "Invoice Value"}, {"field": "outstanding_amount", "function": "sum", "label": "Outstanding"}], "default_chart": "bar", "required_fields": ["supplier", "grand_total", "outstanding_amount"], "drilldown_doctype": "Purchase Invoice"},
    "material_requests_by_status": {"key": "material_requests_by_status", "title": "Material Requests by Status", "module": "Buying", "source_type": "doctype", "source_name": "Material Request", "date_field": "transaction_date", "group_by": ["status"], "metrics": [{"field": "name", "function": "count", "label": "Requests"}], "default_chart": "pie", "required_fields": ["status", "name"], "drilldown_doctype": "Material Request"},
    "unpaid_purchase_invoices": {"key": "unpaid_purchase_invoices", "title": "Unpaid Purchase Invoices", "module": "Buying", "source_type": "doctype", "source_name": "Purchase Invoice", "date_field": "posting_date", "filters": {"status": ["in", ["Unpaid", "Overdue"]]}, "group_by": ["supplier"], "metrics": [{"field": "outstanding_amount", "function": "sum", "label": "Outstanding"}], "default_chart": "bar", "required_fields": ["supplier", "outstanding_amount", "status"], "drilldown_doctype": "Purchase Invoice"},
    "top_suppliers_by_purchase": {"key": "top_suppliers_by_purchase", "title": "Top Suppliers by Purchase Value", "module": "Buying", "source_type": "doctype", "source_name": "Purchase Invoice", "date_field": "posting_date", "group_by": ["supplier"], "metrics": [{"field": "grand_total", "function": "sum", "label": "Purchase Value"}], "default_chart": "bar", "default_limit": 10, "required_fields": ["supplier", "grand_total"], "drilldown_doctype": "Purchase Invoice"},
}

STOCK_ANALYTICS: dict[str, dict[str, Any]] = {
    "items_by_item_group": {"key": "items_by_item_group", "title": "Items by Item Group", "module": "Stock", "source_type": "doctype", "source_name": "Item", "group_by": ["item_group"], "metrics": [{"field": "name", "function": "count", "label": "Items"}], "default_chart": "bar", "required_fields": ["item_group", "name"], "drilldown_doctype": "Item"},
    "stock_entries_by_type": {"key": "stock_entries_by_type", "title": "Stock Entries by Type", "module": "Stock", "source_type": "doctype", "source_name": "Stock Entry", "date_field": "posting_date", "group_by": ["stock_entry_type"], "metrics": [{"field": "name", "function": "count", "label": "Stock Entries"}], "default_chart": "bar", "required_fields": ["stock_entry_type", "name"], "drilldown_doctype": "Stock Entry"},
    "material_requests_by_type": {"key": "material_requests_by_type", "title": "Material Requests by Type", "module": "Stock", "source_type": "doctype", "source_name": "Material Request", "date_field": "transaction_date", "group_by": ["material_request_type"], "metrics": [{"field": "name", "function": "count", "label": "Requests"}], "default_chart": "pie", "required_fields": ["material_request_type", "name"], "drilldown_doctype": "Material Request"},
    "delivery_notes_by_status": {"key": "delivery_notes_by_status", "title": "Delivery Notes by Status", "module": "Stock", "source_type": "doctype", "source_name": "Delivery Note", "date_field": "posting_date", "group_by": ["status"], "metrics": [{"field": "name", "function": "count", "label": "Delivery Notes"}], "default_chart": "pie", "required_fields": ["status", "name"], "drilldown_doctype": "Delivery Note"},
    "purchase_receipts_by_supplier": {"key": "purchase_receipts_by_supplier", "title": "Purchase Receipts by Supplier", "module": "Stock", "source_type": "doctype", "source_name": "Purchase Receipt", "date_field": "posting_date", "group_by": ["supplier"], "metrics": [{"field": "name", "function": "count", "label": "Receipts"}], "default_chart": "bar", "required_fields": ["supplier", "name"], "drilldown_doctype": "Purchase Receipt"},
    "stock_balance": {"key": "stock_balance", "title": "Stock Balance", "module": "Stock", "source_type": "standard_report", "source_name": "Stock Balance", "default_chart": "table"},
    "stock_ledger": {"key": "stock_ledger", "title": "Stock Ledger", "module": "Stock", "source_type": "standard_report", "source_name": "Stock Ledger", "default_chart": "table"},
}

ACCOUNTS_ANALYTICS: dict[str, dict[str, Any]] = {
    "receivables_aging": {"key": "receivables_aging", "title": "Receivables Aging", "module": "Accounts", "source_type": "standard_report", "source_name": "Accounts Receivable", "default_chart": "table"},
    "payables_aging": {"key": "payables_aging", "title": "Payables Aging", "module": "Accounts", "source_type": "standard_report", "source_name": "Accounts Payable", "default_chart": "table"},
    "monthly_sales_vs_purchase": {"key": "monthly_sales_vs_purchase", "title": "Monthly Sales vs Purchase", "module": "Accounts", "source_type": "composite", "source_name": "Sales Invoice + Purchase Invoice", "date_field": "posting_date", "default_chart": "line"},
    "payment_trend": {"key": "payment_trend", "title": "Payment Trend", "module": "Accounts", "source_type": "doctype", "source_name": "Payment Entry", "date_field": "posting_date", "group_by": ["month", "payment_type"], "metrics": [{"field": "paid_amount", "function": "sum", "label": "Paid Amount"}], "default_chart": "line", "required_fields": ["posting_date", "payment_type", "paid_amount"], "drilldown_doctype": "Payment Entry"},
    "journal_entries_by_type": {"key": "journal_entries_by_type", "title": "Journal Entries by Type", "module": "Accounts", "source_type": "doctype", "source_name": "Journal Entry", "date_field": "posting_date", "group_by": ["voucher_type"], "metrics": [{"field": "name", "function": "count", "label": "Entries"}], "default_chart": "bar", "required_fields": ["voucher_type", "name"], "drilldown_doctype": "Journal Entry"},
    "sales_invoices_by_status": {"key": "sales_invoices_by_status", "title": "Sales Invoices by Status", "module": "Accounts", "source_type": "doctype", "source_name": "Sales Invoice", "date_field": "posting_date", "group_by": ["status"], "metrics": [{"field": "name", "function": "count", "label": "Invoices"}, {"field": "grand_total", "function": "sum", "label": "Value"}], "default_chart": "pie", "required_fields": ["status", "name", "grand_total"], "drilldown_doctype": "Sales Invoice"},
    "purchase_invoices_by_status": {"key": "purchase_invoices_by_status", "title": "Purchase Invoices by Status", "module": "Accounts", "source_type": "doctype", "source_name": "Purchase Invoice", "date_field": "posting_date", "group_by": ["status"], "metrics": [{"field": "name", "function": "count", "label": "Invoices"}, {"field": "grand_total", "function": "sum", "label": "Value"}], "default_chart": "pie", "required_fields": ["status", "name", "grand_total"], "drilldown_doctype": "Purchase Invoice"},
}

FUTURE_MODULE_ANALYTICS: dict[str, dict[str, Any]] = {
    "CRM": {},
    "Projects": {},
    "Support": {},
    "HR": {},
    "Assets": {},
    "Manufacturing": {},
}

MODULE_ANALYTICS_REGISTRY: dict[str, dict[str, dict[str, Any]]] = {
    "Selling": SELLING_ANALYTICS,
    "Buying": BUYING_ANALYTICS,
    "Stock": STOCK_ANALYTICS,
    "Accounts": ACCOUNTS_ANALYTICS,
    **FUTURE_MODULE_ANALYTICS,
}

ANALYTICS_CATALOG: dict[str, dict[str, Any]] = {}
for module_definitions in MODULE_ANALYTICS_REGISTRY.values():
    ANALYTICS_CATALOG.update(module_definitions)
