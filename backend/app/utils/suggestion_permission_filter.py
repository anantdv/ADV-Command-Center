from __future__ import annotations

from app.schemas.suggestions import SuggestedPrompt, SuggestionContext


class SuggestionPermissionFilter:
    async def filter(
        self,
        suggestions: list[SuggestedPrompt],
        ctx: SuggestionContext,
        user_roles: list[str],
        cookies: dict | None = None,
    ) -> list[SuggestedPrompt]:
        output: list[SuggestedPrompt] = []
        for suggestion in suggestions:
            item = suggestion.model_copy(deep=True)
            if item.type == "workflow_action":
                action = str(item.payload.get("action") or "")
                if action not in ctx.workflow_actions:
                    continue
            if item.type == "crud_confirmation" and not item.payload.get("confirmation_id"):
                continue
            if item.type == "export":
                if not ctx.message_id or (ctx.row_count or 0) <= 0:
                    continue
            if item.type == "pin":
                if not ctx.message_id or not (ctx.source_name or ctx.doctype or ctx.report_name):
                    continue
            if "selected" in (item.prompt or "").lower() and (ctx.row_count or 0) != 1:
                item.disabled = True
                item.disabled_reason = item.disabled_reason or "Select one row first."
            if item.type in {"workflow_action", "crud_confirmation"}:
                item.requires_confirmation = True
            output.append(item)
        return output
