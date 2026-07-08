from __future__ import annotations

from app.config import settings
from app.core.audit import AuditEvent, log_audit_event
from app.schemas.suggestions import SuggestedPrompt, SuggestionContext, SuggestionResponse
from app.utils.suggestion_permission_filter import SuggestionPermissionFilter
from app.utils.suggestion_rules import get_suggestions_for_context


class SuggestionService:
    def __init__(self, permission_filter: SuggestionPermissionFilter | None = None):
        self.permission_filter = permission_filter or SuggestionPermissionFilter()

    async def generate_suggestions(
        self,
        context: SuggestionContext,
        user_roles: list[str],
        cookies: dict | None = None,
        user: str = "unknown",
    ) -> SuggestionResponse:
        if not settings.enable_dynamic_suggestions:
            return SuggestionResponse(suggestions=[])
        base = get_suggestions_for_context(context)
        filtered = await self.permission_filter.filter(base, context, user_roles, cookies)
        limited = sorted(filtered, key=_rank)[: settings.max_dynamic_suggestions]
        await log_audit_event(AuditEvent(
            user=user,
            conversation_id=context.conversation_id,
            message_id=context.message_id,
            action="suggestions_generated",
            agent_name="suggestion_service",
            tool_name="dynamic_suggestions",
            doctype=context.doctype,
            report_name=context.report_name,
            source_name=context.source_name,
            source_type=context.source_type,
            allowed=True,
            risk_level="low",
            input_summary=f"{context.result_type}:{context.source_name or context.doctype or context.report_name}",
            output_summary=f"{len(limited)} suggestions",
            erp_data_sent=False,
        ))
        return SuggestionResponse(suggestions=limited)


suggestion_service = SuggestionService()


def _rank(item: SuggestedPrompt) -> tuple[int, int, str]:
    label_rank = {
        "Group by Customer": 0,
        "Show Aging": 1,
        "Export to Excel": 2,
        "Pin to Overview": 3,
        "Show Only Overdue": 4,
        "Customer-wise Outstanding": 5,
        "Open Customer Details": 0,
        "Show Customer Invoices": 1,
        "Show Customer Orders": 2,
        "Show Outstanding": 3,
        "Create Quotation Draft": 4,
    }
    if item.label in label_rank:
        return (1 if item.disabled else 0, label_rank[item.label], item.label)
    type_rank = {"workflow_action": 0, "crud_confirmation": 0, "prompt": 1, "export": 2, "pin": 3, "navigation": 4, "action": 5}
    return (1 if item.disabled else 0, type_rank.get(item.type, 9), item.label)
