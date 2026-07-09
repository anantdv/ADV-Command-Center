from app.utils.module_registry import MODULE_REGISTRY, normalize_module_name


def cfg(doctype: str, label: str | None = None, description: str | None = None, icon: str = "file-text", fields: list[str] | None = None, search: list[str] | None = None, order: str = "modified desc") -> dict:
    return {
        "doctype": doctype,
        "label": label or doctype,
        "description": description or f"{doctype} records.",
        "icon": icon,
        "default_fields": fields or ["name", "modified"],
        "search_fields": search or ["name"],
        "default_order_by": order,
    }


ITEM = cfg("Item", "Items", "Products, services, and stock items.", "box", ["name", "item_code", "item_name", "item_group", "stock_uom", "disabled"], ["name", "item_code", "item_name"])
CUSTOMER = cfg("Customer", "Customers", "Customer master records and selling parties.", "users", ["name", "customer_name", "customer_group", "territory", "mobile_no", "email_id"], ["name", "customer_name", "mobile_no", "email_id"])
SUPPLIER = cfg("Supplier", "Suppliers", "Supplier master records and vendor information.", "building-2", ["name", "supplier_name", "supplier_group", "country", "mobile_no", "email_id"], ["name", "supplier_name", "mobile_no", "email_id"])


MODULE_DOCTYPE_REGISTRY = {
    "Selling": [
        CUSTOMER,
        cfg("Lead", "Leads", "Potential customers and early sales prospects.", "user-plus", ["name", "lead_name", "company_name", "status", "email_id", "mobile_no", "creation"], ["name", "lead_name", "company_name", "email_id", "mobile_no"]),
        cfg("Opportunity", "Opportunities", "Sales opportunities and pipeline records.", "target", ["name", "opportunity_from", "party_name", "status", "opportunity_amount", "transaction_date"], ["name", "party_name"]),
        cfg("Quotation", "Quotations", "Customer quotations and estimates.", "file-text", ["name", "quotation_to", "party_name", "transaction_date", "valid_till", "grand_total", "status"], ["name", "party_name"], "transaction_date desc"),
        cfg("Sales Order", "Sales Orders", "Confirmed customer sales orders.", "shopping-cart", ["name", "customer", "transaction_date", "delivery_date", "grand_total", "status"], ["name", "customer"], "transaction_date desc"),
        cfg("Sales Invoice", "Sales Invoices", "Customer invoices and receivables.", "receipt", ["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"], ["name", "customer"], "posting_date desc"),
        cfg("Delivery Note", "Delivery Notes", "Customer delivery and dispatch documents.", "truck", ["name", "customer", "posting_date", "status", "grand_total", "docstatus"], ["name", "customer"], "posting_date desc"),
        ITEM,
    ],
    "Buying": [
        SUPPLIER,
        cfg("Material Request", "Material Requests", "Requests for purchase, transfer, issue, or manufacture.", "clipboard-list", ["name", "material_request_type", "transaction_date", "schedule_date", "status", "docstatus"], ["name", "material_request_type"], "transaction_date desc"),
        cfg("Request for Quotation", "Requests for Quotation", "RFQs sent to suppliers.", "file-question", ["name", "transaction_date", "status", "message_for_supplier"], ["name"], "transaction_date desc"),
        cfg("Supplier Quotation", "Supplier Quotations", "Supplier price quotations.", "file-text", ["name", "supplier", "transaction_date", "valid_till", "grand_total", "status"], ["name", "supplier"], "transaction_date desc"),
        cfg("Purchase Order", "Purchase Orders", "Confirmed purchase orders to suppliers.", "shopping-bag", ["name", "supplier", "transaction_date", "schedule_date", "grand_total", "status"], ["name", "supplier"], "transaction_date desc"),
        cfg("Purchase Receipt", "Purchase Receipts", "Goods receipt records from suppliers.", "package-check", ["name", "supplier", "posting_date", "posting_time", "status", "docstatus"], ["name", "supplier"], "posting_date desc"),
        cfg("Purchase Invoice", "Purchase Invoices", "Supplier invoices and payables.", "receipt", ["name", "supplier", "posting_date", "bill_no", "bill_date", "grand_total", "outstanding_amount", "status"], ["name", "supplier", "bill_no"], "posting_date desc"),
        ITEM,
    ],
    "Stock": [
        ITEM,
        cfg("Warehouse", "Warehouses", "Warehouse and storage locations.", "warehouse", ["name", "warehouse_name", "parent_warehouse", "company", "is_group", "disabled"], ["name", "warehouse_name"]),
        cfg("Stock Entry", "Stock Entries", "Material transfer, receipt, issue, and manufacture entries.", "repeat", ["name", "stock_entry_type", "posting_date", "posting_time", "purpose", "docstatus"], ["name", "stock_entry_type", "purpose"], "posting_date desc"),
        cfg("Stock Reconciliation", "Stock Reconciliations", "Stock balance reconciliation records.", "scale", ["name", "posting_date", "posting_time", "purpose", "docstatus"], ["name", "purpose"], "posting_date desc"),
        cfg("Stock Ledger Entry", "Stock Ledger Entries", "Stock movement ledger entries.", "list-tree", ["name", "item_code", "warehouse", "posting_date", "actual_qty", "qty_after_transaction"], ["name", "item_code", "warehouse"], "posting_date desc"),
        cfg("Delivery Note", "Delivery Notes", "Outgoing stock delivery records.", "truck", ["name", "customer", "posting_date", "status", "docstatus"], ["name", "customer"], "posting_date desc"),
        cfg("Purchase Receipt", "Purchase Receipts", "Incoming stock receipt records.", "package-check", ["name", "supplier", "posting_date", "status", "docstatus"], ["name", "supplier"], "posting_date desc"),
        cfg("Material Request", "Material Requests", "Material planning and stock requests.", "clipboard-list", ["name", "material_request_type", "transaction_date", "schedule_date", "status"], ["name", "material_request_type"], "transaction_date desc"),
        cfg("Batch", "Batches", "Batch tracking records.", "layers", ["name", "batch_id", "item", "expiry_date", "disabled"], ["name", "batch_id", "item"]),
        cfg("Serial No", "Serial Numbers", "Serialized item tracking.", "barcode", ["name", "item_code", "warehouse", "status", "purchase_date", "delivery_document_no"], ["name", "item_code"]),
    ],
    "Accounts": [
        cfg("Sales Invoice", "Sales Invoices", "Customer invoices and receivables.", "receipt", ["name", "customer", "posting_date", "due_date", "grand_total", "outstanding_amount", "status"], ["name", "customer"], "posting_date desc"),
        cfg("Purchase Invoice", "Purchase Invoices", "Supplier invoices and payables.", "receipt-text", ["name", "supplier", "posting_date", "bill_no", "bill_date", "grand_total", "outstanding_amount", "status"], ["name", "supplier", "bill_no"], "posting_date desc"),
        cfg("Payment Entry", "Payment Entries", "Incoming and outgoing payment records.", "credit-card", ["name", "payment_type", "party_type", "party", "posting_date", "paid_amount", "status"], ["name", "party"], "posting_date desc"),
        cfg("Journal Entry", "Journal Entries", "Accounting journal vouchers.", "book-open", ["name", "voucher_type", "posting_date", "total_debit", "total_credit", "docstatus"], ["name", "voucher_type"], "posting_date desc"),
        cfg("GL Entry", "GL Entries", "General ledger entries.", "list", ["name", "account", "posting_date", "voucher_type", "voucher_no", "debit", "credit"], ["name", "account", "voucher_no"], "posting_date desc"),
        cfg("Account", "Accounts", "Chart of accounts.", "landmark", ["name", "account_name", "account_number", "parent_account", "root_type", "is_group"], ["name", "account_name", "account_number"]),
        cfg("Cost Center", "Cost Centers", "Cost center hierarchy.", "network", ["name", "cost_center_name", "parent_cost_center", "company", "is_group"], ["name", "cost_center_name"]),
        cfg("Mode of Payment", "Modes of Payment", "Payment modes and accounts.", "wallet", ["name", "mode_of_payment", "type", "enabled"], ["name", "mode_of_payment"]),
    ],
    "CRM": [
        cfg("Lead", "Leads", "Potential customers and prospects.", "user-plus", ["name", "lead_name", "company_name", "status", "email_id", "mobile_no"], ["name", "lead_name", "company_name"]),
        cfg("Opportunity", "Opportunities", "Sales pipeline opportunities.", "target", ["name", "opportunity_from", "party_name", "status", "opportunity_amount", "transaction_date"], ["name", "party_name"]),
        CUSTOMER,
        cfg("Contact", "Contacts", "Contact people and communication details.", "contact", ["name", "first_name", "last_name", "email_id", "mobile_no"], ["name", "first_name", "last_name", "email_id"]),
        cfg("Address", "Addresses", "Party address records.", "map-pin", ["name", "address_title", "address_type", "city", "country"], ["name", "address_title", "city"]),
        cfg("Communication", "Communications", "Email and communication records.", "mail", ["name", "subject", "communication_type", "status", "creation"], ["name", "subject"]),
        cfg("CRM Note", "CRM Notes", "CRM notes and follow-ups.", "sticky-note", ["name", "title", "creation", "modified"], ["name", "title"]),
    ],
    "Projects": [
        cfg("Project", "Projects", "Project master records.", "kanban", ["name", "project_name", "status", "percent_complete", "expected_start_date", "expected_end_date"], ["name", "project_name"]),
        cfg("Task", "Tasks", "Project task records.", "check-square", ["name", "subject", "project", "status", "exp_start_date", "exp_end_date"], ["name", "subject", "project"]),
        cfg("Timesheet", "Timesheets", "Timesheet and time logging records.", "clock", ["name", "employee", "start_date", "end_date", "total_hours", "status"], ["name", "employee"], "modified desc"),
        cfg("Project Template", "Project Templates", "Reusable project templates.", "copy", ["name", "project_type"], ["name", "project_type"]),
        cfg("Activity Type", "Activity Types", "Time tracking activity types.", "activity", ["name", "activity_type", "disabled"], ["name", "activity_type"]),
    ],
    "Support": [
        cfg("Issue", "Issues", "Support tickets and customer issues.", "life-buoy", ["name", "subject", "customer", "priority", "status", "issue_type", "creation"], ["name", "subject", "customer"], "modified desc"),
        cfg("Issue Type", "Issue Types", "Support issue categories.", "tags", ["name", "description"], ["name", "description"]),
        CUSTOMER,
        cfg("Contact", "Contacts", "Support contact records.", "contact", ["name", "first_name", "last_name", "email_id", "mobile_no"], ["name", "first_name", "last_name", "email_id"]),
        cfg("Communication", "Communications", "Support communications.", "mail", ["name", "subject", "communication_type", "status", "creation"], ["name", "subject"]),
        cfg("Service Level Agreement", "Service Level Agreements", "SLA policies and targets.", "timer", ["name", "default_service_level_agreement", "enabled"], ["name"]),
    ],
    "HR": [
        cfg("Employee", "Employees", "Employee master records.", "id-card", ["name", "employee_name", "department", "designation", "status"], ["name", "employee_name", "department"]),
        cfg("Attendance", "Attendance", "Employee attendance records.", "calendar-check", ["name", "employee", "employee_name", "attendance_date", "status"], ["name", "employee", "employee_name"], "attendance_date desc"),
        cfg("Leave Application", "Leave Applications", "Employee leave requests.", "calendar-minus", ["name", "employee", "employee_name", "leave_type", "from_date", "to_date", "status"], ["name", "employee", "employee_name"], "from_date desc"),
        cfg("Leave Type", "Leave Types", "Leave policy types.", "calendar", ["name", "leave_type_name", "is_lwp"], ["name", "leave_type_name"]),
        cfg("Salary Slip", "Salary Slips", "Payroll salary slip records.", "receipt-text", ["name", "employee", "employee_name", "start_date", "end_date", "status"], ["name", "employee", "employee_name"], "modified desc"),
        cfg("Payroll Entry", "Payroll Entries", "Payroll processing records.", "wallet", ["name", "company", "payroll_frequency", "start_date", "end_date", "status"], ["name", "company"], "modified desc"),
        cfg("Expense Claim", "Expense Claims", "Employee expense claims.", "wallet-cards", ["name", "employee", "employee_name", "posting_date", "total_claimed_amount", "status"], ["name", "employee", "employee_name"], "posting_date desc"),
        cfg("Department", "Departments", "Company department records.", "building", ["name", "department_name", "parent_department", "company"], ["name", "department_name"]),
        cfg("Designation", "Designations", "Employee designations.", "badge", ["name", "designation_name"], ["name", "designation_name"]),
    ],
    "Assets": [
        cfg("Asset", "Assets", "Fixed asset records.", "boxes", ["name", "asset_name", "asset_category", "location", "status", "gross_purchase_amount"], ["name", "asset_name", "asset_category"]),
        cfg("Asset Category", "Asset Categories", "Asset category records.", "folder-tree", ["name", "asset_category_name"], ["name", "asset_category_name"]),
        cfg("Asset Movement", "Asset Movements", "Asset movement records.", "move", ["name", "transaction_date", "purpose", "company", "docstatus"], ["name", "purpose"], "transaction_date desc"),
        cfg("Asset Maintenance", "Asset Maintenance", "Asset maintenance schedules.", "wrench", ["name", "asset_name", "maintenance_status", "next_due_date"], ["name", "asset_name"]),
        cfg("Asset Repair", "Asset Repairs", "Asset repair records.", "hammer", ["name", "asset", "repair_status", "failure_date", "completion_date"], ["name", "asset"], "modified desc"),
        cfg("Location", "Locations", "Location master records.", "map-pin", ["name", "location_name", "parent_location", "is_group"], ["name", "location_name"]),
    ],
    "Manufacturing": [
        cfg("BOM", "BOMs", "Bill of materials records.", "factory", ["name", "item", "quantity", "is_active", "is_default"], ["name", "item"]),
        cfg("Work Order", "Work Orders", "Manufacturing work orders.", "factory", ["name", "production_item", "qty", "produced_qty", "status", "planned_start_date"], ["name", "production_item"], "planned_start_date desc"),
        cfg("Production Plan", "Production Plans", "Production planning records.", "calendar-cog", ["name", "company", "posting_date", "status"], ["name", "company"], "posting_date desc"),
        cfg("Job Card", "Job Cards", "Shop-floor job cards.", "clipboard-check", ["name", "work_order", "operation", "workstation", "status"], ["name", "work_order", "operation"]),
        cfg("Operation", "Operations", "Manufacturing operations.", "settings", ["name", "operation"], ["name", "operation"]),
        cfg("Workstation", "Workstations", "Manufacturing workstation records.", "monitor-cog", ["name", "workstation_name", "production_capacity", "disabled"], ["name", "workstation_name"]),
        ITEM,
    ],
}


def module_doctypes(module_name: str) -> list[dict]:
    normalized = normalize_module_name(module_name)
    configured = MODULE_DOCTYPE_REGISTRY.get(normalized)
    if configured:
        return configured
    return [cfg(doctype) for doctype in MODULE_REGISTRY.get(normalized, {}).get("doctypes", [])]


def find_module_doctype(module_name: str, doctype: str) -> dict | None:
    return next((item for item in module_doctypes(module_name) if item["doctype"].lower() == doctype.lower()), None)
