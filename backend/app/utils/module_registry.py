MODULE_REGISTRY = {
    "Selling": {
        "label": "Selling",
        "route": "/modules/selling",
        "icon": "shopping-cart",
        "description": "Customers, quotations, sales orders, invoices, and sales analytics.",
        "category": "Revenue",
        "doctypes": ["Customer", "Lead", "Opportunity", "Quotation", "Sales Order", "Sales Invoice", "Delivery Note", "Item"],
        "reports": ["Sales Analytics", "Sales Register", "Item-wise Sales Register", "Customer-wise Sales Register", "Sales Order Trends"],
    },
    "Buying": {
        "label": "Buying",
        "route": "/modules/buying",
        "icon": "package-check",
        "description": "Suppliers, purchase orders, purchase invoices, and procurement analytics.",
        "category": "Procurement",
        "doctypes": ["Supplier", "Request for Quotation", "Supplier Quotation", "Purchase Order", "Purchase Invoice", "Purchase Receipt", "Material Request", "Item"],
        "reports": ["Purchase Analytics", "Purchase Register", "Item-wise Purchase Register", "Supplier-wise Sales Analytics"],
    },
    "Stock": {
        "label": "Stock",
        "route": "/modules/stock",
        "icon": "warehouse",
        "description": "Items, warehouses, stock balance, movement, and inventory analytics.",
        "category": "Inventory",
        "doctypes": ["Item", "Warehouse", "Stock Entry", "Stock Reconciliation", "Delivery Note", "Purchase Receipt"],
        "reports": ["Stock Balance", "Stock Ledger", "Stock Projected Qty", "Item Price Stock"],
    },
    "Accounts": {
        "label": "Accounts",
        "route": "/modules/accounts",
        "icon": "landmark",
        "description": "Invoices, payments, journal entries, receivables, payables, and ledger reports.",
        "category": "Finance",
        "doctypes": ["Sales Invoice", "Purchase Invoice", "Payment Entry", "Journal Entry", "GL Entry", "Account"],
        "reports": ["General Ledger", "Accounts Receivable", "Accounts Payable", "Trial Balance", "Balance Sheet", "Profit and Loss Statement"],
    },
    "CRM": {
        "label": "CRM",
        "route": "/modules/crm",
        "icon": "handshake",
        "description": "Leads, opportunities, campaigns, and customer relationship workflows.",
        "category": "Revenue",
        "doctypes": ["Lead", "Opportunity", "Customer", "Contact"],
        "reports": [],
    },
    "Projects": {
        "label": "Projects",
        "route": "/modules/projects",
        "icon": "briefcase-business",
        "description": "Projects, tasks, time tracking, and delivery status.",
        "category": "Operations",
        "doctypes": ["Project", "Task", "Timesheet"],
        "reports": [],
    },
    "HR": {
        "label": "HR",
        "route": "/modules/hr",
        "icon": "users-round",
        "description": "Employee records, leave, attendance, and HR workflows.",
        "category": "People",
        "doctypes": ["Employee", "Leave Application", "Attendance"],
        "reports": [],
    },
    "Manufacturing": {
        "label": "Manufacturing",
        "route": "/modules/manufacturing",
        "icon": "factory",
        "description": "Work orders, BOMs, production plans, and shop-floor operations.",
        "category": "Operations",
        "doctypes": ["Work Order", "BOM", "Production Plan", "Job Card"],
        "reports": [],
    },
}


def normalize_module_name(value: str) -> str:
    text = (value or "").strip().replace("-", " ").replace("_", " ").lower()
    aliases = {"accounting": "Accounts", "accounts": "Accounts", "selling": "Selling", "buying": "Buying", "stock": "Stock", "crm": "CRM", "projects": "Projects", "hr": "HR", "manufacturing": "Manufacturing"}
    return aliases.get(text, " ".join(part.capitalize() for part in text.split()))
