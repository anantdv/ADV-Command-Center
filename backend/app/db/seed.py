"""Central mock fixtures used by demo services."""

MOCK_USER = {
    "user": "admin@example.com",
    "full_name": "Admin User",
    "roles": ["System Manager", "Accounts Manager"],
    "company": "ABC Corporation",
    "company_currency": "INR",
    "allowed_companies": ["ABC Corporation"],
    "timezone": "Asia/Kolkata",
    "language": "en",
}

FULL_PERMISSION = {"can_read": True, "can_write": True, "can_create": True, "can_delete": False, "can_submit": True, "can_cancel": False, "can_export": True}

MODULES = [
    ("accounting", "Accounting", "Ledgers, receivables, payables and financial reporting.", "₹12.4L", "Net profit", "indigo"),
    ("selling", "Selling", "Customers, quotations, sales orders and invoicing.", "₹42.3L", "Sales this month", "blue"),
    ("buying", "Buying", "Suppliers, purchase orders and procurement cycles.", "84", "Open orders", "amber"),
    ("stock", "Stock", "Items, warehouses, ledgers and reorder intelligence.", "₹24.1L", "Stock value", "emerald"),
    ("crm", "CRM", "Leads, opportunities and relationship management.", "126", "Active leads", "violet"),
    ("projects", "Projects", "Project delivery, tasks, timesheets and billing.", "18", "Active projects", "cyan"),
    ("hr", "HR", "Employees, attendance, payroll and performance.", "248", "Employees", "rose"),
    ("manufacturing", "Manufacturing", "BOMs, work orders and production planning.", "31", "Open work orders", "orange"),
]

MODULE_RECORDS = {
    "accounting": ["Trial Balance", "General Ledger", "Accounts Receivable", "Accounts Payable", "Journal Entry", "Payment Entry"],
    "selling": ["Customers", "Quotations", "Sales Orders", "Sales Invoices", "Sales Analytics"],
    "buying": ["Suppliers", "Request for Quotation", "Purchase Orders", "Purchase Receipts", "Purchase Invoices"],
    "stock": ["Items", "Warehouses", "Stock Ledger", "Stock Balance", "Reorder Report"],
    "crm": ["Leads", "Opportunities", "Prospects", "Appointments", "Sales Pipeline"],
    "projects": ["Projects", "Tasks", "Timesheets", "Activity Cost", "Project Billing"],
    "hr": ["Employees", "Attendance", "Leave Applications", "Payroll Entry", "Performance"],
    "manufacturing": ["Bill of Materials", "Work Orders", "Job Cards", "Production Plan", "Quality Inspection"],
}

INVOICES = [
    {"id": "SINV-2026-0418", "customer": "Aster Retail Pvt Ltd", "due": "04 Jun 2026", "days": 27, "amount": "₹1,84,500", "risk": "High"},
    {"id": "SINV-2026-0397", "customer": "Nimbus Labs India", "due": "11 Jun 2026", "days": 20, "amount": "₹1,42,800", "risk": "Medium"},
    {"id": "SINV-2026-0362", "customer": "Orbit Works", "due": "18 Jun 2026", "days": 13, "amount": "₹98,750", "risk": "Low"},
    {"id": "SINV-2026-0341", "customer": "BluePeak Systems", "due": "21 Jun 2026", "days": 10, "amount": "₹76,200", "risk": "Medium"},
]
