from app.tools.base import ToolDefinition


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def list(self) -> list[ToolDefinition]:
        return list(self._tools.values())


registry = ToolRegistry()

# Only low-risk read tools are executable during this stage.
for name, description, permission in [
    ("get_current_user_context", "Get ERPNext user context", "read"),
    ("get_allowed_doctypes", "List allowed DocTypes", "read"),
    ("get_doctype_schema", "Read an allowed DocType schema", "read"),
    ("list_records", "List permission-filtered ERP records", "read"),
    ("get_record", "Read one permission-filtered ERP record", "read"),
    ("run_report", "Run an approved ERP report", "report"),
    ("generate_chart", "Build chart configuration from returned rows", "read"),
]:
    registry.register(
        ToolDefinition(
            name=name,
            description=description,
            risk_level="low",
            requires_confirmation=False,
            permission_required=permission,
            input_schema={"type": "object"},
        )
    )

for name, description in [
    ("generate_excel", "Generate a private Excel file from permission-approved rows"),
    ("generate_csv", "Generate a private CSV file from permission-approved rows"),
    ("generate_pdf", "Generate a private PDF from permission-approved rows"),
    ("generate_chart_png", "Render a private PNG from an approved chart result"),
    ("generate_html_report", "Generate a private HTML report from permission-approved rows"),
    ("save_to_library", "Register a generated private file in the AI Library"),
]:
    registry.register(ToolDefinition(name=name, description=description, risk_level="medium", requires_confirmation=False, permission_required="export", input_schema={"type": "object"}))

for name, description, risk in [
    ("pin_to_dashboard", "Pin a refreshable read-only result to Overview", "medium"),
    ("refresh_dashboard_widget", "Refresh a widget through ERP APIs", "low"),
    ("create_dashboard_widget", "Create AI dashboard metadata", "medium"),
    ("delete_dashboard_widget", "Delete AI dashboard metadata", "medium"),
]:
    registry.register(ToolDefinition(name=name, description=description, risk_level=risk, requires_confirmation=False, permission_required="read", input_schema={"type":"object"}))

for name, description, permission in [
    ("prepare_create_record", "Prepare an allowlisted draft record creation for review", "create"),
    ("prepare_update_record", "Prepare an allowlisted safe field update for review", "write"),
    ("confirm_crud_action", "Execute one previously confirmed controlled CRUD action", "write"),
    ("cancel_crud_action", "Cancel a pending controlled CRUD confirmation", "write"),
]:
    registry.register(ToolDefinition(name=name, description=description, risk_level="medium", requires_confirmation=name == "confirm_crud_action", permission_required=permission, input_schema={"type": "object"}))

for name, description, permission in [
    ("search_approved_knowledge", "Search role-filtered approved private knowledge", "read"),
    ("answer_from_approved_knowledge", "Draft a cited answer from approved knowledge", "read"),
    ("generate_training_assessment", "Generate a quiz from approved training chunks", "training"),
    ("answer_support_question", "Answer support questions from approved knowledge", "read"),
    ("create_support_ticket", "Escalate unresolved help through the Frappe support API", "create"),
]:
    registry.register(ToolDefinition(name=name,description=description,risk_level="medium" if permission in {"training","create"} else "low",requires_confirmation=permission=="create",permission_required=permission,input_schema={"type":"object"}))

for name, description, permission in [
    ("upload_document_intake", "Upload a private business document for local OCR intake", "create"),
    ("extract_ocr_text", "Extract text locally from an uploaded PDF/image", "read"),
    ("build_document_mapping_preview", "Map extracted fields to a draft ERPNext document preview", "create"),
    ("get_report_available_columns", "Resolve readable columns for a DocType/report", "read"),
    ("run_report_with_columns", "Run a report with selected columns", "read"),
    ("diagnose_report", "Diagnose report execution and response normalization", "read"),
]:
    registry.register(ToolDefinition(name=name,description=description,risk_level="medium" if permission=="create" else "low",requires_confirmation=False,permission_required=permission,input_schema={"type":"object"}))
