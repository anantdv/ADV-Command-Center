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
        suggestions = []
        if (ctx.row_count or 0) > 0:
            suggestions.append(_prompt("Open First Document", "Open the first pending approval document", "open_first", group="workflow"))
        suggestions.extend([
            _prompt("Show Sales Invoice Approvals", "Show my pending Sales Invoice approvals", "sales_invoice_approvals", group="workflow"),
            _prompt("Show Purchase Order Approvals", "Show my pending Purchase Order approvals", "purchase_order_approvals", group="workflow"),
            _prompt("Refresh", ctx.previous_prompt or "Show my pending approvals", "refresh", group="workflow"),
        ])
        return suggestions
    if ctx.result_type == "workflow_detail":
        for action in ctx.workflow_actions:
            suggestions.append(SuggestedPrompt(id=_id("wf", action), label=action, type="workflow_action", action_type="preview_workflow_action", payload={"doctype": ctx.doctype, "name": ctx.document_name, "action": action}, risk="medium", requires_confirmation=True, group="workflow"))
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
    result_id = _result_id(ctx)
    missing = None if result_id else "This action needs a saved result context."
    transform_payload = _transform_payload(ctx, result_id)
    return [
        SuggestedPrompt(id=_id("export", "xlsx"), label="Export to Excel", type="export", action_type="export_result", payload={"result_id": result_id, "format": "xlsx", "conversation_id": ctx.conversation_id, "message_id": ctx.message_id}, icon="file-spreadsheet", disabled=not result_id, disabled_reason=missing, group="share"),
        SuggestedPrompt(id=_id("export", "pdf"), label="Export to PDF", type="export", action_type="export_result", payload={"result_id": result_id, "format": "pdf", "conversation_id": ctx.conversation_id, "message_id": ctx.message_id}, icon="file-down", disabled=not result_id, disabled_reason=missing, group="share"),
        SuggestedPrompt(id=_id("pin", "overview"), label="Pin to Overview", type="pin", action_type="pin_to_dashboard", payload={"result_id": result_id, "target_type": "overview", "conversation_id": ctx.conversation_id, "message_id": ctx.message_id}, icon="pin", disabled=not result_id, disabled_reason=missing, group="share"),
        SuggestedPrompt(id=_id("ui", "change_columns"), label="Change Columns", type="ui_action", action_type="open_column_selector_dialog", payload={"result_id": result_id, "columns": ctx.columns}, icon="columns", disabled=not result_id, disabled_reason=missing, group="view"),
        SuggestedPrompt(id=_id("action", "summarize_chart"), label="Summarize as Chart", type="action", prompt=_same("Summarize this result as a chart", ctx), action_type="transform_report", payload={**transform_payload, "operation": "visualize", "visualization": "auto", "preserve_grouping": True}, disabled=not result_id, disabled_reason=missing, group="view"),
    ]


def _doctype_suggestions(ctx: SuggestionContext) -> list[SuggestedPrompt]:
    doctype = ctx.doctype or ctx.source_name
    if doctype == "Sales Invoice":
        suggestions = [
            SuggestedPrompt(id=_id("action", "group_customer"), label="Group by Customer", type="action", prompt=_same("Group these sales invoices by customer with total amount and outstanding amount", ctx), action_type="transform_report", payload={**_transform_payload(ctx, _result_id(ctx)), "operation": "regroup", "group_by": "customer"}, group="analysis", disabled=not _result_id(ctx), disabled_reason=None if _result_id(ctx) else "This action needs a saved result context."),
            _prompt("Show Aging", "Show receivables aging for these sales invoices", "show_aging", group="analysis"),
            _prompt("Show Only Overdue", _same("Show only overdue sales invoices for the same period", ctx), "only_overdue", group="analysis"),
            _prompt("Customer-wise Outstanding", _same("Show customer-wise outstanding for these sales invoices", ctx), "customer_outstanding", group="analysis"),
            SuggestedPrompt(id=_id("action", "monthly_trend"), label="Monthly Trend", type="action", prompt=_same("Show monthly sales invoice trend for the same period", ctx), action_type="transform_report", payload={**_transform_payload(ctx, _result_id(ctx)), "operation": "regroup", "group_by": "month"}, group="analysis", disabled=not _result_id(ctx), disabled_reason=None if _result_id(ctx) else "This action needs a saved result context."),
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
    if ctx.result_type not in {"chart", "analytics", "report_composer"}:
        return []
    result_id = _result_id(ctx)
    missing = None if result_id else "This chart action needs an active result. Please rerun the report and try again."
    base_payload = {
        "result_id": result_id,
        "source_type": ctx.source_type,
        "source_name": ctx.source_name,
        "doctype": ctx.doctype,
        "report_name": ctx.report_name,
        "filters": ctx.filters,
        "columns": ctx.columns,
        "current_chart_type": ctx.chart_type,
    }
    suggestions = [
        _prompt("Show Details", f"Show detail records for {ctx.source_name or ctx.doctype or 'this report'}", "show_details", group="analysis"),
        SuggestedPrompt(id=_id("ui", "save_report_view"), label="Save Report View", type="ui_action", action_type="open_save_report_view_dialog", payload=base_payload, disabled=not result_id, disabled_reason=missing, group="analysis"),
        SuggestedPrompt(id=_id("ui", "change_chart_type"), label="Change Chart Type", type="ui_action", action_type="open_chart_type_dialog", payload={**base_payload, "available_chart_types": ["bar", "line", "area", "pie", "donut"]}, disabled=not result_id, disabled_reason=missing, group="view"),
        SuggestedPrompt(id=_id("ui", "refine_filters"), label="Refine Filters", type="ui_action", action_type="open_refine_filters_dialog", payload=base_payload, disabled=not result_id, disabled_reason=missing, group="view"),
        SuggestedPrompt(id=_id("ui", "pin"), label="Pin", type="ui_action", action_type="open_pin_target_dialog", payload=base_payload, disabled=not result_id, disabled_reason=missing, group="share"),
    ]
    if ctx.chart_type != "bar":
        suggestions.append(SuggestedPrompt(id=_id("action", "bar_chart"), label="Convert to Bar Chart", type="action", action_type="convert_chart_type", payload={**base_payload, "chart_type": "bar"}, disabled=not result_id, disabled_reason=missing, group="view"))
    if ctx.chart_type != "line" and _looks_time_series(ctx):
        suggestions.append(SuggestedPrompt(id=_id("action", "line_chart"), label="Convert to Line Chart", type="action", action_type="convert_chart_type", payload={**base_payload, "chart_type": "line"}, disabled=not result_id, disabled_reason=missing, group="view"))
    suggestions.append(_prompt("Monthly Trend", "show monthly trend for this report", "monthly_trend", group="analysis"))
    return suggestions


def _transform_payload(ctx: SuggestionContext, result_id: str | None) -> dict:
    return {
        "action": "transform_report",
        "report_id": ctx.extra.get("report_id"),
        "result_id": result_id,
        "source_type": ctx.source_type,
        "source_name": ctx.source_name,
        "doctype": ctx.doctype,
        "report_name": ctx.report_name,
        "filters": ctx.filters,
        "columns": ctx.columns,
        "preserve_filters": True,
        "conversation_id": ctx.conversation_id,
        "message_id": ctx.message_id,
        "source": "generated_action",
    }


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


def _result_id(ctx: SuggestionContext) -> str | None:
    result_id = ctx.extra.get("result_id") or ctx.message_id
    return str(result_id) if result_id else None
