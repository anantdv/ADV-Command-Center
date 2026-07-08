from __future__ import annotations

from app.schemas.suggestions import SuggestedPrompt, SuggestionContext
from app.utils.ids import new_id


def get_suggestions_for_context(ctx: SuggestionContext) -> list[SuggestedPrompt]:
    suggestions: list[SuggestedPrompt] = []
    if ctx.result_type == "error":
        return [_prompt("Retry", ctx.previous_prompt or "Try that query again", "retry"), _prompt("Rephrase Query", "Rephrase the last query more simply", "rephrase")]
    if ctx.result_type == "empty":
        return [_prompt("Remove Filters", _same("Show the same records without filters", ctx), "remove_filters"), _prompt("Broaden Date Range", _same("Search the same records for this year", ctx), "broaden_date"), _prompt("Search All Records", f"Show all {ctx.doctype or ctx.source_name or 'records'}", "search_all")]
    if ctx.result_type == "workflow_pending_list":
        return [
            _prompt("Open First Document", "Open the first pending approval document", "open_first", group="workflow"),
            _prompt("Show Sales Invoice Approvals", "Show my pending Sales Invoice approvals", "sales_invoice_approvals", group="workflow"),
            _prompt("Show Purchase Order Approvals", "Show my pending Purchase Order approvals", "purchase_order_approvals", group="workflow"),
            _prompt("Refresh", ctx.previous_prompt or "Show my pending approvals", "refresh", group="workflow"),
        ]
    if ctx.result_type == "workflow_detail":
        for action in ctx.workflow_actions:
            suggestions.append(SuggestedPrompt(id=_id("wf", action), label=action, type="workflow_action", action_type="apply_workflow_action", payload={"doctype": ctx.doctype, "name": ctx.document_name, "action": action}, risk="medium", requires_confirmation=True, group="workflow"))
        suggestions.append(_prompt("Refresh", ctx.previous_prompt or "Refresh this workflow document", "refresh", group="workflow"))
        return suggestions
    if ctx.result_type == "crud_preview":
        return [
            SuggestedPrompt(id=_id("crud", "confirm"), label="Confirm Draft", type="crud_confirmation", action_type="confirm_draft", payload={"confirmation_id": ctx.extra.get("confirmation_id")}, risk="medium", requires_confirmation=True, group="draft"),
            _prompt("Edit Fields", "Edit the draft fields before confirming", "edit_fields", group="draft"),
            SuggestedPrompt(id=_id("crud", "cancel"), label="Cancel", type="crud_confirmation", action_type="cancel_draft", payload={"confirmation_id": ctx.extra.get("confirmation_id")}, risk="low", group="draft"),
        ]
    if ctx.result_type == "file_generated":
        return [
            SuggestedPrompt(id=_id("file", "download"), label="Download", type="navigation", action_type="download_file", payload={"download_url": ctx.extra.get("download_url")}, icon="download"),
            SuggestedPrompt(id=_id("file", "library"), label="Open Library", type="navigation", action_type="open_library", icon="library"),
            _prompt("Generate Another Format", f"Generate another format for {ctx.source_name or 'this result'}", "another_format", group="file"),
        ]

    if (ctx.row_count or 0) > 0 and ctx.result_type in {"table", "chart", "analytics", "report_composer", "document_detail"}:
        suggestions.extend(_doctype_suggestions(ctx))
        suggestions.extend(_analytics_suggestions(ctx))
        suggestions.extend(_general_table_suggestions(ctx))
    return _dedupe(suggestions)


def _general_table_suggestions(ctx: SuggestionContext) -> list[SuggestedPrompt]:
    if not ctx.message_id:
        return []
    return [
        SuggestedPrompt(id=_id("export", "xlsx"), label="Export to Excel", type="export", action_type="export_result", payload={"format": "xlsx", "conversation_id": ctx.conversation_id, "message_id": ctx.message_id}, icon="file-spreadsheet", group="share"),
        SuggestedPrompt(id=_id("export", "pdf"), label="Export to PDF", type="export", action_type="export_result", payload={"format": "pdf", "conversation_id": ctx.conversation_id, "message_id": ctx.message_id}, icon="file-down", group="share"),
        SuggestedPrompt(id=_id("pin", "overview"), label="Pin to Overview", type="pin", action_type="pin_to_dashboard", payload={"conversation_id": ctx.conversation_id, "message_id": ctx.message_id}, icon="pin", group="share"),
        _prompt("Change Columns", _same("Change columns for this result", ctx), "change_columns", group="view"),
        _prompt("Summarize as Chart", _same("Summarize this result as a chart", ctx), "summarize_chart", group="view"),
    ]


def _doctype_suggestions(ctx: SuggestionContext) -> list[SuggestedPrompt]:
    doctype = ctx.doctype or ctx.source_name
    if doctype == "Sales Invoice":
        suggestions = [
            _prompt("Group by Customer", _same("Group these sales invoices by customer with total amount and outstanding amount", ctx), "group_customer", group="analysis"),
            _prompt("Show Aging", "Show receivables aging for these sales invoices", "show_aging", group="analysis"),
            _prompt("Show Only Overdue", _same("Show only overdue sales invoices for the same period", ctx), "only_overdue", group="analysis"),
            _prompt("Customer-wise Outstanding", _same("Show customer-wise outstanding for these sales invoices", ctx), "customer_outstanding", group="analysis"),
            _prompt("Monthly Trend", _same("Show monthly sales invoice trend for the same period", ctx), "monthly_trend", group="analysis"),
        ]
        if _status_is(ctx, {"unpaid", "overdue"}):
            suggestions.append(_prompt("Collection Follow-up Draft", "Create collection follow-up drafts for these overdue invoices", "collection_followup", disabled=True, disabled_reason="Email drafting for collections is not enabled yet.", risk="medium", group="draft"))
        return suggestions
    if doctype == "Customer":
        single = (ctx.row_count or 0) == 1 and bool(ctx.document_name)
        return [
            _prompt("Open Customer Details", f"Show customer {ctx.document_name}" if single else "Open customer details", "open_customer", disabled=not single, disabled_reason=None if single else "Select one customer first.", group="customer"),
            _prompt("Show Customer Invoices", f"Show sales invoices for customer {ctx.document_name}" if single else "Show invoices for selected customer", "customer_invoices", disabled=not single, disabled_reason=None if single else "Select one customer first.", group="customer"),
            _prompt("Show Customer Orders", f"Show sales orders for customer {ctx.document_name}" if single else "Show orders for selected customer", "customer_orders", disabled=not single, disabled_reason=None if single else "Select one customer first.", group="customer"),
            _prompt("Show Outstanding", f"Show outstanding for customer {ctx.document_name}" if single else "Show outstanding for selected customer", "customer_outstanding", disabled=not single, disabled_reason=None if single else "Select one customer first.", group="customer"),
            _prompt("Create Quotation Draft", f"Create quotation draft for customer {ctx.document_name}" if single else "Create quotation draft for selected customer", "quotation_draft", disabled=not single, disabled_reason=None if single else "Select one customer first.", risk="medium", group="draft"),
        ]
    if doctype == "Supplier":
        return [_prompt("Show Supplier Invoices", "Show purchase invoices for this supplier", "supplier_invoices"), _prompt("Show Purchase Orders", "Show purchase orders for this supplier", "supplier_orders"), _prompt("Show Outstanding Payable", "Show outstanding payable for this supplier", "supplier_payable"), _prompt("Create Purchase Order Draft", "Create purchase order draft for this supplier", "po_draft", risk="medium")]
    if doctype == "Item":
        return [_prompt("Show Stock Balance", "Show stock balance for this item", "stock_balance"), _prompt("Show Sales for Item", "Show sales for this item", "item_sales"), _prompt("Show Purchase History", "Show purchase history for this item", "item_purchase"), _prompt("Show Item Movement", "Show item movement for this item", "item_movement"), _prompt("Create Material Request Draft", "Create material request draft for this item", "mr_draft", risk="medium")]
    if doctype == "Purchase Order":
        return [_prompt("Group by Supplier", "Group these purchase orders by supplier with total amount", "po_by_supplier"), _prompt("Show Pending Receipts", "Show pending receipts for these purchase orders", "pending_receipts"), _prompt("Show Purchase Trend", "Show purchase order trend for the same period", "po_trend")]
    return []


def _analytics_suggestions(ctx: SuggestionContext) -> list[SuggestedPrompt]:
    if ctx.result_type not in {"analytics", "report_composer"}:
        return []
    suggestions = [
        _prompt("Show Details", f"Show detail records for {ctx.source_name or ctx.doctype or 'this report'}", "show_details", group="analysis"),
        _prompt("Save Report View", "Save this report view", "save_report_view", group="analysis"),
        _prompt("Change Chart Type", "Change chart type for this report", "change_chart", group="view"),
    ]
    if ctx.chart_type != "bar":
        suggestions.append(_prompt("Convert to Bar Chart", "Convert this result to a bar chart", "bar_chart", group="view"))
    if ctx.chart_type != "line" and _looks_time_series(ctx):
        suggestions.append(_prompt("Convert to Line Chart", "Convert this result to a line chart", "line_chart", group="view"))
    return suggestions


def _prompt(label: str, prompt: str, key: str, *, disabled: bool = False, disabled_reason: str | None = None, risk: str = "low", group: str | None = None) -> SuggestedPrompt:
    return SuggestedPrompt(id=_id("prompt", key), label=label, type="prompt", prompt=prompt, risk=risk, disabled=disabled, disabled_reason=disabled_reason, group=group)


def _same(prompt: str, ctx: SuggestionContext) -> str:
    if ctx.filters:
        return f"{prompt}. Use the same filters."
    return prompt


def _id(prefix: str, key: str) -> str:
    clean = "".join(ch if ch.isalnum() else "_" for ch in key.lower()).strip("_")
    return f"sug_{prefix}_{clean}" or new_id("sug")


def _dedupe(items: list[SuggestedPrompt]) -> list[SuggestedPrompt]:
    seen: set[str] = set()
    output: list[SuggestedPrompt] = []
    for item in items:
        if item.label in seen:
            continue
        seen.add(item.label)
        output.append(item)
    return output


def _status_is(ctx: SuggestionContext, values: set[str]) -> bool:
    status = str((ctx.filters or {}).get("status") or "").lower()
    return any(value in status for value in values)


def _looks_time_series(ctx: SuggestionContext) -> bool:
    return any(column in {"period", "month", "posting_date", "transaction_date", "creation"} for column in ctx.columns)
