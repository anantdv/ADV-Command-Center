from __future__ import annotations

from app.schemas.task_plan import ExecutionPlan, PlanAction, PlanType


class TaskPlanValidator:
    """Validates execution plans before the deterministic executor runs."""

    WRITE_ACTIONS = {PlanAction.CREATE_DRAFT, PlanAction.SUBMIT, PlanAction.CANCEL, PlanAction.DELETE, PlanAction.SEND_EMAIL}

    def validate(self, plan: ExecutionPlan) -> list[str]:
        errors: list[str] = []
        step_ids = {step.id for step in plan.steps}
        for step in plan.steps:
            missing = [item for item in step.depends_on if item not in step_ids]
            if missing:
                errors.append(f"Step {step.id} depends on unknown step(s): {', '.join(missing)}")
        if plan.type not in {PlanType.DRAFT_CREATE, PlanType.DRAFT_CONTINUE, PlanType.WORKFLOW}:
            for step in plan.steps:
                if step.action in self.WRITE_ACTIONS:
                    errors.append(f"{step.action.value} is not allowed in {plan.type.value} plans.")
        if plan.type == PlanType.DRAFT_CREATE and not any(step.action == PlanAction.PREVIEW for step in plan.steps):
            errors.append("Draft creation plans must generate a preview before confirmation.")
        return errors


task_plan_validator = TaskPlanValidator()

