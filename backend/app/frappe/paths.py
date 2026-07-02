"""Whitelisted AI Command Center companion method paths."""

GET_CURRENT_USER_CONTEXT = "/api/method/ai_command_center.api.auth.get_current_user_context"
GET_ALLOWED_DOCTYPES = "/api/method/ai_command_center.api.schema.get_allowed_doctypes"
GET_DOCTYPE_SCHEMA = "/api/method/ai_command_center.api.schema.get_doctype_schema"
CHECK_PERMISSION = "/api/method/ai_command_center.api.permissions.check_permission"

LIST_RECORDS = "/api/method/ai_command_center.api.crud.list_records"
GET_RECORD = "/api/method/ai_command_center.api.crud.get_record"
CREATE_RECORD = "/api/method/ai_command_center.api.crud.create_record"
UPDATE_RECORD = "/api/method/ai_command_center.api.crud.update_record"

RUN_REPORT = "/api/method/ai_command_center.api.reports.run_report"
GET_ALLOWED_REPORTS = "/api/method/ai_command_center.api.reports.get_allowed_reports"

GET_WIDGET_DATA = "/api/method/ai_command_center.api.dashboards.get_widget_data"
SAVE_DASHBOARD_WIDGET = "/api/method/ai_command_center.api.dashboards.save_dashboard_widget"
LIST_DASHBOARD_WIDGETS = "/api/method/ai_command_center.api.dashboards.list_dashboard_widgets"
GET_DASHBOARD_WIDGET = "/api/method/ai_command_center.api.dashboards.get_dashboard_widget"
UPDATE_DASHBOARD_WIDGET = "/api/method/ai_command_center.api.dashboards.update_dashboard_widget"
DELETE_DASHBOARD_WIDGET = "/api/method/ai_command_center.api.dashboards.delete_dashboard_widget"
REORDER_DASHBOARD_WIDGETS = "/api/method/ai_command_center.api.dashboards.reorder_dashboard_widgets"

REGISTER_GENERATED_FILE = "/api/method/ai_command_center.api.files.register_generated_file"
LIST_GENERATED_FILES = "/api/method/ai_command_center.api.files.list_generated_files"

CREATE_SUPPORT_TICKET = "/api/method/ai_command_center.api.support.create_support_ticket"
LIST_SUPPORT_TICKETS = "/api/method/ai_command_center.api.support.list_support_tickets"

CREATE_AUDIT_LOG = "/api/method/ai_command_center.api.audit.create_audit_log"
