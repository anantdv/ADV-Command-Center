from __future__ import annotations

from app.agents.router_agent import IntentResult
from app.schemas.chat import ChatMessageRequest
from app.schemas.conversation_state import ConversationContext, StateDecision
from app.schemas.task_plan import ExecutionPlan, PlanAction, PlanStatus, PlanStep, PlanType
from app.utils.datetime import utc_now
from app.utils.ids import new_id


class TaskPlanner:
    """Converts commands into deterministic execution plans.

    The planner describes what should happen, but intentionally does not call
    ERPNext or mutate any draft/report data.
    """

    def create_plan(
        self,
        request: ChatMessageRequest,
        context: ConversationContext,
        decision: StateDecision,
        intent: IntentResult | None = None,
        followup: dict | None = None,
    ) -> ExecutionPlan:
        now = utc_now()
        plan_type = self._plan_type(decision, intent, followup)
        title = self._title(plan_type, intent, request)
        plan = ExecutionPlan(
            id=new_id("plan"),
            conversation_id=context.conversation_id,
            type=plan_type,
            title=title,
            status=PlanStatus.PENDING,
            draft_session_id=context.draft_session_id,
            report_session_id=context.report_session_id,
            active_doctype=(intent.doctype if intent else None) or context.active_doctype,
            active_document=(intent.record_name if intent else None) or context.active_document,
            source_message=request.message,
            route=decision.route,
            steps=self._steps(plan_type, intent, followup),
            created_at=now,
            updated_at=now,
            metadata={
                "source": request.source or "typed",
                "structured_action": request.structured_action or {},
                "state_reason": decision.reason,
                "normalized_message": decision.normalized_message,
                "graph_enabled": True,
                "graph_scope": {
                    "doctype": (intent.doctype if intent else None) or context.active_doctype,
                    "name": (intent.record_name if intent else None) or context.active_document,
                    "mode": "lazy_permission_checked",
                },
            },
        )
        if plan.steps:
            plan.current_step_id = plan.steps[0].id
        return plan

    def _plan_type(self, decision: StateDecision, intent: IntentResult | None, followup: dict | None) -> PlanType:
        if followup:
            return PlanType.REPORT_FOLLOWUP
        if decision.route in {"structured_selection", "structured_draft_field", "draft_continue"}:
            return PlanType.DRAFT_CONTINUE
        if intent:
            if intent.intent == "crud_create":
                return PlanType.DRAFT_CREATE
            if intent.intent in {"list_records", "run_report", "run_analytics", "report_composer", "summary_query", "chart_query"}:
                return PlanType.REPORT
            if intent.intent == "get_record":
                return PlanType.RECORD_DETAIL
            if intent.intent == "generate_file":
                return PlanType.FILE_GENERATION
            if intent.intent.startswith("workflow_"):
                return PlanType.WORKFLOW
        if decision.route == "new_draft":
            return PlanType.DRAFT_CREATE
        return PlanType.GENERAL

    def _title(self, plan_type: PlanType, intent: IntentResult | None, request: ChatMessageRequest) -> str:
        if plan_type in {PlanType.DRAFT_CREATE, PlanType.DRAFT_CONTINUE}:
            return f"Prepare {intent.doctype if intent and intent.doctype else 'ERPNext Draft'}"
        if plan_type in {PlanType.REPORT, PlanType.REPORT_FOLLOWUP}:
            return f"Run {intent.report_name or intent.doctype if intent else 'ERPNext Report'}"
        if plan_type == PlanType.RECORD_DETAIL:
            return f"Open {intent.doctype or 'Document'} {intent.record_name or ''}".strip() if intent else "Open Document"
        if plan_type == PlanType.FILE_GENERATION:
            return "Generate File"
        if plan_type == PlanType.WORKFLOW:
            return "Workflow Action"
        return request.message[:80]

    def _steps(self, plan_type: PlanType, intent: IntentResult | None, followup: dict | None) -> list[PlanStep]:
        if plan_type == PlanType.DRAFT_CREATE:
            parent_label = self._parent_resolution_label(intent.doctype if intent else None)
            return [
                self._step("1", PlanAction.RESOLVE_ENTITY, parent_label),
                self._step("2", PlanAction.RESOLVE_ITEMS, "Resolve child rows and items", ["1"]),
                self._step("3", PlanAction.RESOLVE_WAREHOUSE, "Resolve warehouse and defaults", ["2"]),
                self._step("4", PlanAction.DISCOVER_RELATIONSHIPS, "Inspect related defaults and dependencies", ["3"]),
                self._step("5", PlanAction.VALIDATE, "Validate required fields", ["4"]),
                self._step("6", PlanAction.PREVIEW, "Generate draft preview", ["5"]),
                self._step("7", PlanAction.CONFIRM, "Wait for confirmation", ["6"]),
                self._step("8", PlanAction.CREATE_DRAFT, "Create ERPNext draft", ["7"]),
            ]
        if plan_type == PlanType.DRAFT_CONTINUE:
            return [
                self._step("1", PlanAction.RESOLVE_ENTITY, "Apply user selection or input"),
                self._step("2", PlanAction.MUTATE_DRAFT, "Update DraftSession", ["1"]),
                self._step("3", PlanAction.VALIDATE, "Validate refreshed draft", ["2"]),
                self._step("4", PlanAction.PREVIEW, "Refresh preview", ["3"]),
            ]
        if plan_type == PlanType.REPORT:
            return [
                self._step("1", PlanAction.VALIDATE, "Validate report request"),
                self._step("2", PlanAction.RUN_REPORT, "Run permission-checked ERPNext query", ["1"]),
                self._step("3", PlanAction.GENERATE_CHART, "Prepare chart/table presentation", ["2"]),
            ]
        if plan_type == PlanType.REPORT_FOLLOWUP:
            operation = str((followup or {}).get("operation") or "visualize")
            action = PlanAction.GENERATE_CHART if operation in {"visualize", "regroup"} else PlanAction.EXPORT if operation == "export" else PlanAction.RUN_REPORT
            return [
                self._step("1", PlanAction.VALIDATE, "Load active report context"),
                self._step("2", action, f"Apply report follow-up: {operation}", ["1"]),
            ]
        if plan_type == PlanType.RECORD_DETAIL:
            return [
                self._step("1", PlanAction.VALIDATE, "Resolve document type and name"),
                self._step("2", PlanAction.GET_RECORD, "Fetch permission-checked document detail", ["1"]),
                self._step("3", PlanAction.DISCOVER_RELATIONSHIPS, "Discover related business documents", ["2"]),
            ]
        if plan_type == PlanType.FILE_GENERATION:
            return [
                self._step("1", PlanAction.VALIDATE, "Validate export request"),
                self._step("2", PlanAction.EXPORT, "Generate file from allowed data", ["1"]),
            ]
        if plan_type == PlanType.WORKFLOW:
            return [
                self._step("1", PlanAction.VALIDATE, "Validate workflow request"),
                self._step("2", PlanAction.CONFIRM, "Require workflow confirmation", ["1"]),
            ]
        return [self._step("1", PlanAction.VALIDATE, "Classify command")]

    @staticmethod
    def _parent_resolution_label(doctype: str | None) -> str:
        if doctype in {"Sales Order", "Sales Invoice", "Delivery Note"}:
            return "Resolve Customer"
        if doctype in {"Purchase Order", "Purchase Invoice", "Purchase Receipt"}:
            return "Resolve Supplier"
        if doctype == "Quotation":
            return "Resolve Quotation Party"
        if doctype == "Stock Entry":
            return "Resolve warehouses"
        return "Resolve parent Link fields"

    def create_confirmation_plan(self, confirmation: dict, source_message: str | None = None) -> ExecutionPlan:
        now = utc_now()
        doctype = str(confirmation.get("doctype") or "ERPNext Document")
        operation = str(confirmation.get("operation") or "create")
        conversation_id = str(confirmation.get("conversation_id") or new_id("conv"))
        return ExecutionPlan(
            id=new_id("plan"),
            conversation_id=conversation_id,
            type=PlanType.DRAFT_CONTINUE,
            title=f"Confirm {operation} {doctype}",
            status=PlanStatus.PENDING,
            draft_session_id=conversation_id,
            active_doctype=doctype,
            active_document=confirmation.get("record_name"),
            source_message=source_message or f"confirm {operation} {doctype}",
            route="confirmation",
            current_step_id="1",
            steps=[
                self._step("1", PlanAction.VALIDATE, "Re-check ERPNext permissions"),
                self._step("2", PlanAction.CONFIRM, "Validate confirmation token", ["1"]),
                self._step("3", PlanAction.CREATE_DRAFT, "Create or update ERPNext draft", ["2"]),
            ],
            created_at=now,
            updated_at=now,
            metadata={"confirmation_id": confirmation.get("confirmation_id"), "operation": operation},
        )

    @staticmethod
    def _step(step_id: str, action: PlanAction, label: str, depends_on: list[str] | None = None) -> PlanStep:
        return PlanStep(id=step_id, action=action, label=label, depends_on=depends_on or [])


task_planner = TaskPlanner()
