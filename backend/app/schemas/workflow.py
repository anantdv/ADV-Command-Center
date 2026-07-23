from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from app.schemas.common import CamelModel


class WorkflowAction(CamelModel):
    action: str
    next_state: str | None = None
    allowed: bool = True
    label: str | None = None


class WorkflowDocumentContext(CamelModel):
    doctype: str
    name: str
    workflow_state: str | None = None
    available_actions: list[WorkflowAction] = Field(default_factory=list)
    source_message_id: str | None = None
    source_result_id: str | None = None


class WorkflowActionPreviewRequest(CamelModel):
    doctype: str
    name: str
    action: str
    comment: str | None = None


class WorkflowActionPreviewResponse(CamelModel):
    doctype: str
    name: str
    action: str
    current_state: str | None = None
    next_state: str | None = None
    title: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    confirmation_required: bool = True
    confirmation_id: str


class PendingWorkflowDocument(CamelModel):
    doctype: str
    name: str
    title: str | None = None
    workflow_state: str | None = None
    status: str | None = None
    owner: str | None = None
    modified: str | None = None
    posting_date: str | None = None
    transaction_date: str | None = None
    party: str | None = None
    grand_total: float | None = None
    currency: str | None = None
    available_actions: list[WorkflowAction] = Field(default_factory=list)


class PendingApprovalsResponse(CamelModel):
    documents: list[PendingWorkflowDocument]
    total: int
    filters: dict[str, Any] = Field(default_factory=dict)


class WorkflowDocumentDetail(CamelModel):
    doctype: str
    name: str
    title: str | None = None
    workflow_state: str | None = None
    status: str | None = None
    docstatus: int | None = None
    summary: dict[str, Any] = Field(default_factory=dict)
    fields: dict[str, Any] = Field(default_factory=dict)
    items: list[dict[str, Any]] = Field(default_factory=list)
    available_actions: list[WorkflowAction] = Field(default_factory=list)
    permission: dict[str, Any] | None = None


class ApplyWorkflowActionRequest(CamelModel):
    doctype: str
    name: str
    action: str
    comment: str | None = None
    confirmation_id: str


class ApplyWorkflowActionResponse(CamelModel):
    doctype: str
    name: str
    action: str
    previous_state: str | None = None
    new_state: str | None = None
    status: str | None = None
    available_actions: list[WorkflowAction] = Field(default_factory=list)
    message: str
    result: dict[str, Any] = Field(default_factory=dict)
