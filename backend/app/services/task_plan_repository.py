from __future__ import annotations

from app.schemas.task_plan import ExecutionPlan


class InMemoryTaskPlanRepository:
    """Persistence boundary for execution plans.

    TODO: replace with SQLAlchemy tables so plan resume survives process restarts.
    """

    def __init__(self) -> None:
        self.plans: dict[str, ExecutionPlan] = {}
        self.by_conversation: dict[str, list[str]] = {}

    async def save(self, plan: ExecutionPlan) -> ExecutionPlan:
        self.plans[plan.id] = plan
        ids = self.by_conversation.setdefault(plan.conversation_id, [])
        if plan.id not in ids:
            ids.append(plan.id)
        return plan

    async def get(self, plan_id: str) -> ExecutionPlan | None:
        return self.plans.get(plan_id)

    async def latest_for_conversation(self, conversation_id: str) -> ExecutionPlan | None:
        ids = self.by_conversation.get(conversation_id) or []
        for plan_id in reversed(ids):
            plan = self.plans.get(plan_id)
            if plan:
                return plan
        return None

    async def list_for_conversation(self, conversation_id: str) -> list[ExecutionPlan]:
        return [self.plans[item] for item in self.by_conversation.get(conversation_id, []) if item in self.plans]


task_plan_repository = InMemoryTaskPlanRepository()

