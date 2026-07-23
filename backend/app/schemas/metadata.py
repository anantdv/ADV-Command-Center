from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

from app.schemas.common import PermissionMeta


FieldImportance = Literal["required", "recommended", "optional", "hidden", "read_only", "computed"]


class FieldIntelligence(BaseModel):
    fieldname: str
    label: str
    fieldtype: str
    required: bool = False
    read_only: bool = False
    hidden: bool = False
    permlevel: int = 0
    options: str | None = None
    link_to: str | None = None
    child_doctype: str | None = None
    depends_on: str | None = None
    fetch_from: str | None = None
    default: Any = None
    description: str | None = None
    help_text: str | None = None
    aliases: list[str] = Field(default_factory=list)
    examples: list[str] = Field(default_factory=list)
    importance: FieldImportance = "optional"
    writable: bool = True
    searchable: bool = False
    section: str | None = None


class ChildTableIntelligence(BaseModel):
    fieldname: str
    label: str
    child_doctype: str
    required: bool = False
    link_fields: list[FieldIntelligence] = Field(default_factory=list)
    editable_fields: list[FieldIntelligence] = Field(default_factory=list)
    required_fields: list[str] = Field(default_factory=list)
    field_priority: list[str] = Field(default_factory=list)


class WorkflowIntelligence(BaseModel):
    is_submittable: bool = False
    workflow_state_field: str | None = None
    states: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)


class SearchIntelligence(BaseModel):
    title_field: str | None = None
    search_fields: list[str] = Field(default_factory=list)
    display_fields: list[str] = Field(default_factory=list)


class FormLayoutIntelligence(BaseModel):
    sections: list[dict[str, Any]] = Field(default_factory=list)
    tabs: list[dict[str, Any]] = Field(default_factory=list)
    fields: list[FieldIntelligence] = Field(default_factory=list)
    child_tables: list[ChildTableIntelligence] = Field(default_factory=list)


class DoctypeIntelligence(BaseModel):
    doctype: str
    module: str | None = None
    title_field: str | None = None
    naming_rule: str | None = None
    autoname: str | None = None
    is_submittable: bool = False
    is_tree: bool = False
    is_nested_set: bool = False
    allow_rename: bool = False
    allow_copy: bool = False
    track_changes: bool = False
    fields: list[FieldIntelligence]
    child_tables: list[ChildTableIntelligence] = Field(default_factory=list)
    mandatory_fields: list[str] = Field(default_factory=list)
    writable_fields: list[str] = Field(default_factory=list)
    link_fields: list[FieldIntelligence] = Field(default_factory=list)
    search: SearchIntelligence = Field(default_factory=SearchIntelligence)
    workflow: WorkflowIntelligence = Field(default_factory=WorkflowIntelligence)
    permissions: PermissionMeta = Field(default_factory=PermissionMeta)
    form: FormLayoutIntelligence | None = None
    cache_key: str | None = None
    diagnostics: dict[str, Any] = Field(default_factory=dict)


class DocumentInspectionResponse(BaseModel):
    doctype: str
    name: str | None = None
    metadata: DoctypeIntelligence
    missing_required_fields: list[str] = Field(default_factory=list)
    workflow_state: str | None = None
    available_actions: list[dict[str, Any]] = Field(default_factory=list)
    links: list[dict[str, Any]] = Field(default_factory=list)

