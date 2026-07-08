from app.schemas.suggestions import SuggestionContext
from app.utils.suggestion_rules import get_suggestions_for_context


def labels(ctx: SuggestionContext) -> list[str]:
    return [item.label for item in get_suggestions_for_context(ctx)]


def test_sales_invoice_table_returns_invoice_specific_suggestions():
    ctx = SuggestionContext(result_type="table", doctype="Sales Invoice", source_name="Sales Invoice", row_count=14, message_id="msg_1", conversation_id="conv_1", filters={"status": "Unpaid"}, columns=["name", "customer", "outstanding_amount"])
    names = labels(ctx)
    assert "Group by Customer" in names
    assert "Show Aging" in names
    assert "Export to Excel" in names
    assert "Pin to Overview" in names
    assert "Collection Follow-up Draft" in names


def test_customer_result_returns_customer_suggestions():
    ctx = SuggestionContext(result_type="table", doctype="Customer", source_name="Customer", row_count=1, document_name="CUST-0001", message_id="msg_1", conversation_id="conv_1")
    names = labels(ctx)
    assert {"Open Customer Details", "Show Customer Invoices", "Show Customer Orders", "Show Outstanding", "Create Quotation Draft"} <= set(names)


def test_analytics_result_returns_export_pin_change_chart():
    ctx = SuggestionContext(result_type="analytics", doctype="Sales Invoice", source_name="Sales Invoice", row_count=10, message_id="msg_1", conversation_id="conv_1", chart_type="line", columns=["period", "grand_total_sum"])
    names = labels(ctx)
    assert "Export to Excel" in names
    assert "Pin to Overview" in names
    assert "Change Chart Type" in names
    assert "Convert to Bar Chart" in names


def test_workflow_and_crud_suggestions():
    workflow = labels(SuggestionContext(result_type="workflow_pending_list", row_count=2))
    assert "Open First Document" in workflow
    assert "Show Sales Invoice Approvals" in workflow

    detail = get_suggestions_for_context(SuggestionContext(result_type="workflow_detail", doctype="Sales Invoice", document_name="SINV-1", workflow_actions=["Approve"]))
    assert detail[0].type == "workflow_action"
    assert detail[0].requires_confirmation is True

    crud = labels(SuggestionContext(result_type="crud_preview", extra={"confirmation_id": "conf_1"}))
    assert {"Confirm Draft", "Edit Fields", "Cancel"} <= set(crud)


def test_empty_and_error_suggestions():
    assert "Broaden Date Range" in labels(SuggestionContext(result_type="empty", doctype="Sales Invoice"))
    assert "Retry" in labels(SuggestionContext(result_type="error", previous_prompt="show customers"))
