from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class PlanType(str, Enum):
    DRAFT_CREATE = "draft_create"
    DRAFT_CONTINUE = "draft_continue"
    REPORT = "report"
    REPORT_FOLLOWUP = "report_followup"
    RECORD_DETAIL = "record_detail"
    FILE_GENERATION = "file_generation"
    WORKFLOW = "workflow"
    GENERAL = "general"


class PlanAction(str, Enum):
    RESOLVE_ENTITY = "ResolveEntity"
    RESOLVE_ITEMS = "ResolveItems"
    RESOLVE_WAREHOUSE = "ResolveWarehouse"
    RESOLVE_COMPANY = "ResolveCompany"
    RESOLVE_CURRENCY = "ResolveCurrency"
    RESOLVE_TAXES = "ResolveTaxes"
    RESOLVE_RATES = "ResolveRates"
    RESOLVE_PROJECT = "ResolveProject"
    RESOLVE_COST_CENTER = "ResolveCostCenter"
    COLLECT_MISSING_FIELDS = "CollectMissingFields"
    VALIDATE = "Validate"
    PREVIEW = "Preview"
    CONFIRM = "Confirm"
    CREATE_DRAFT = "CreateDraft"
    SUBMIT = "Submit"
    CANCEL = "Cancel"
    DELETE = "Delete"
    RUN_REPORT = "RunReport"
    EXPORT = "Export"
    GENERATE_CHART = "GenerateChart"
    SEND_EMAIL = "SendEmail"
    CREATE_REMINDER = "CreateReminder"
    GET_RECORD = "GetRecord"
    INSPECT_DRAFT = "InspectDraft"
    MUTATE_DRAFT = "MutateDraft"
    DISCOVER_RELATIONSHIPS = "DiscoverRelationships"
    GRAPH_REASONING = "GraphReasoning"


class PlanStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING_USER = "waiting_user"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    SKIPPED = "skipped"


class PlanStep(BaseModel):
    id: str
    action: PlanAction
    label: str
    status: PlanStatus = PlanStatus.PENDING
    depends_on: list[str] = Field(default_factory=list)
    input: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ExecutionPlan(BaseModel):
    id: str
    conversation_id: str
    type: PlanType
    title: str
    status: PlanStatus = PlanStatus.PENDING
    draft_session_id: str | None = None
    report_session_id: str | None = None
    active_doctype: str | None = None
    active_document: str | None = None
    source_message: str | None = None
    route: str | None = None
    current_step_id: str | None = None
    resume_point: str | None = None
    steps: list[PlanStep] = Field(default_factory=list)
    results: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class PlanStepView(BaseModel):
    id: str
    label: str
    action: str
    status: PlanStatus


class PlanPart(BaseModel):
    type: Literal["execution_plan"] = "execution_plan"
    plan_id: str
    title: str
    status: PlanStatus
    current_step_id: str | None = None
    steps: list[PlanStepView]
    resume_point: str | None = None
