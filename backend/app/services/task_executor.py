from __future__ import annotations

import logging
from time import perf_counter
from typing import Awaitable, Callable, TypeVar

from app.core.audit import AuditEvent, log_audit_event
from app.schemas.task_plan import ExecutionPlan, PlanAction, PlanPart, PlanStatus, PlanStepView
from app.services.task_plan_repository import InMemoryTaskPlanRepository, task_plan_repository
from app.utils.datetime import utc_now

logger = logging.getLogger(__name__)
T = TypeVar("T")


class TaskExecutor:
    """Runs validated execution plans deterministically around existing services.

    The executor owns step state changes. It delegates actual ERPNext reads/writes
    only to the existing permission-aware services passed in as callbacks.
    """

    def __init__(self, repository: InMemoryTaskPlanRepository | None = None) -> None:
        self.repository = repository or task_plan_repository

    async def run(self, plan: ExecutionPlan, operation: Callable[[], Awaitable[T]], user: str = "unknown") -> tuple[T, ExecutionPlan]:
        started = perf_counter()
        await self._mark(plan, PlanStatus.RUNNING)
        try:
            if plan.steps:
                await self._mark_step(plan, plan.steps[0].id, PlanStatus.RUNNING)
            result = await operation()
            await self._complete_for_result(plan, result)
            await self._audit("execution_plan_completed", plan, user, int((perf_counter() - started) * 1000))
            return result, plan
        except Exception as exc:
            if plan.current_step_id:
                await self._mark_step(plan, plan.current_step_id, PlanStatus.FAILED, str(exc))
            await self._mark(plan, PlanStatus.FAILED)
            await self._audit("execution_plan_failed", plan, user, int((perf_counter() - started) * 1000), str(exc))
            raise

    async def cancel(self, plan_id: str, user: str = "unknown") -> ExecutionPlan | None:
        plan = await self.repository.get(plan_id)
        if not plan:
            return None
        for step in plan.steps:
            if step.status in {PlanStatus.PENDING, PlanStatus.RUNNING, PlanStatus.WAITING_USER}:
                step.status = PlanStatus.CANCELLED
        await self._mark(plan, PlanStatus.CANCELLED)
        await self._audit("execution_plan_cancelled", plan, user, 0)
        return plan

    async def retry(self, plan_id: str, user: str = "unknown") -> ExecutionPlan | None:
        plan = await self.repository.get(plan_id)
        if not plan:
            return None
        failed = next((step for step in plan.steps if step.status == PlanStatus.FAILED), None)
        if failed:
            failed.status = PlanStatus.PENDING
            failed.error = None
            plan.current_step_id = failed.id
            plan.status = PlanStatus.PENDING
            plan.updated_at = utc_now()
            await self.repository.save(plan)
            await self._audit("execution_plan_retry_requested", plan, user, 0)
        return plan

    async def _complete_for_result(self, plan: ExecutionPlan, result: object) -> None:
        intent = getattr(result, "intent", "")
        if intent in {"child_rows_resolution_required", "draft_field_options"}:
            status = PlanStatus.WAITING_USER
            resume = "user_selection"
        elif intent in {"crud_create", "crud_update", "draft_preview_updated"}:
            status = PlanStatus.WAITING_USER
            resume = "confirmation"
        else:
            status = PlanStatus.COMPLETED
            resume = None
        waiting_action = self._waiting_action_for_result(result)
        if status == PlanStatus.WAITING_USER and waiting_action:
            for step in plan.steps:
                if step.action == waiting_action:
                    step.status = PlanStatus.WAITING_USER
                    plan.current_step_id = step.id
                    break
                if step.status in {PlanStatus.PENDING, PlanStatus.RUNNING}:
                    step.status = PlanStatus.COMPLETED
                    step.completed_at = utc_now()
            plan.status = status
            plan.resume_point = resume
            plan.updated_at = utc_now()
            await self.repository.save(plan)
            return
        for step in plan.steps:
            if step.status == PlanStatus.RUNNING:
                step.status = PlanStatus.COMPLETED
                step.completed_at = utc_now()
            elif status == PlanStatus.COMPLETED and step.status == PlanStatus.PENDING:
                step.status = PlanStatus.COMPLETED
                step.completed_at = utc_now()
            elif status == PlanStatus.WAITING_USER and step.status == PlanStatus.PENDING:
                step.status = PlanStatus.WAITING_USER
                plan.current_step_id = step.id
                break
        plan.status = status
        plan.resume_point = resume
        plan.updated_at = utc_now()
        await self.repository.save(plan)

    @staticmethod
    def _waiting_action_for_result(result: object) -> PlanAction | None:
        intent = getattr(result, "intent", "")
        parts = getattr(result, "parts", []) or []
        if intent == "draft_field_options":
            option_part = next((part for part in parts if getattr(part, "type", "") == "draft_field_options"), None)
            if getattr(option_part, "fieldname", "") == "warehouse":
                return PlanAction.RESOLVE_WAREHOUSE
            return PlanAction.RESOLVE_ENTITY
        if intent != "child_rows_resolution_required":
            return None
        resolution = next((part for part in parts if getattr(part, "type", "") == "child_rows_resolution_required"), None)
        rows = getattr(resolution, "rows", []) or []
        if any(str(getattr(row, "row_id", "")).startswith("parent-") or getattr(row, "link_field", "") != "item_code" for row in rows):
            return PlanAction.RESOLVE_ENTITY
        if rows:
            return PlanAction.RESOLVE_ITEMS
        return None

    async def _mark(self, plan: ExecutionPlan, status: PlanStatus) -> None:
        plan.status = status
        plan.updated_at = utc_now()
        await self.repository.save(plan)

    async def _mark_step(self, plan: ExecutionPlan, step_id: str, status: PlanStatus, error: str | None = None) -> None:
        for step in plan.steps:
            if step.id == step_id:
                step.status = status
                step.error = error
                if status == PlanStatus.RUNNING:
                    step.started_at = utc_now()
                if status in {PlanStatus.COMPLETED, PlanStatus.FAILED, PlanStatus.CANCELLED, PlanStatus.SKIPPED}:
                    step.completed_at = utc_now()
                break
        plan.current_step_id = step_id
        plan.updated_at = utc_now()
        await self.repository.save(plan)

    async def _audit(self, action: str, plan: ExecutionPlan, user: str, duration_ms: int, error: str | None = None) -> None:
        logger.info("execution_plan_event", extra={
            "conversation_id": plan.conversation_id,
            "plan_id": plan.id,
            "plan_type": plan.type.value,
            "status": plan.status.value,
            "current_step_id": plan.current_step_id,
            "duration_ms": duration_ms,
            "error": error,
        })
        await log_audit_event(AuditEvent(user=user, conversation_id=plan.conversation_id, action=action, agent_name="task_executor", tool_name="execution_plan", allowed=error is None, risk_level="medium", input_summary=f"{plan.type.value}:{plan.title}", output_summary=plan.status.value, status=plan.status.value, latency_ms=duration_ms))


def plan_part(plan: ExecutionPlan) -> PlanPart:
    return PlanPart(
        plan_id=plan.id,
        title=plan.title,
        status=plan.status,
        current_step_id=plan.current_step_id,
        resume_point=plan.resume_point,
        steps=[PlanStepView(id=step.id, label=step.label, action=step.action.value, status=step.status) for step in plan.steps],
    )


task_executor = TaskExecutor()
