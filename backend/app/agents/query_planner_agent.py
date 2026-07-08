from __future__ import annotations

from app.schemas.query_plan import QueryPlan
from app.services.query_planner_service import QueryPlannerService


class QueryPlannerAgent:
    """Agent wrapper that produces a QueryPlan only; it never fetches ERP data."""

    def __init__(self, service: QueryPlannerService | None = None):
        self.service = service or QueryPlannerService()

    async def handle(
        self,
        message: str,
        module_context: str | None = None,
        current_date: str | None = None,
        user: str = "unknown",
        conversation_id: str | None = None,
        cookies: dict | None = None,
    ) -> QueryPlan:
        _ = cookies  # Explicitly unused: planning must not receive ERP session data.
        return await self.service.plan(message, module_context, current_date, user, conversation_id)
