from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class GraphNodeType(str, Enum):
    DOCUMENT = "document"
    MASTER = "master"
    TRANSACTION = "transaction"
    CHILD_ROW = "child_row"
    SYSTEM = "system"


class GraphEdgeType(str, Enum):
    LINKS_TO = "LINKS_TO"
    CONTAINS = "CONTAINS"
    PARENT_OF = "PARENT_OF"
    GENERATED = "GENERATED"
    PAID_BY = "PAID_BY"
    POSTED_TO = "POSTED_TO"
    ASSIGNED_TO = "ASSIGNED_TO"
    RELATED_TO = "RELATED_TO"
    BLOCKED_BY = "BLOCKED_BY"
    DEPENDS_ON = "DEPENDS_ON"


class GraphNode(BaseModel):
    id: str
    doctype: str
    name: str
    label: str | None = None
    node_type: GraphNodeType = GraphNodeType.DOCUMENT
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    id: str
    source_id: str
    target_id: str
    edge_type: GraphEdgeType
    label: str
    fieldname: str | None = None
    confidence: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphNeighborhood(BaseModel):
    root: GraphNode
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    depth: int = 1
    truncated: bool = False


class GraphTraversalRequest(BaseModel):
    doctype: str
    name: str
    direction: str = "both"
    depth: int = Field(default=1, ge=1, le=4)
    limit: int = Field(default=50, ge=1, le=200)


class GraphPath(BaseModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    explanation: str


class RelatedDocumentsResponse(BaseModel):
    doctype: str
    name: str
    related: GraphNeighborhood


class TimelineEvent(BaseModel):
    id: str
    doctype: str
    name: str
    label: str
    event_type: str
    event_date: str | None = None
    status: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BusinessTimeline(BaseModel):
    root: GraphNode
    events: list[TimelineEvent]


class ReasoningRequest(BaseModel):
    question: str
    doctype: str | None = None
    name: str | None = None
    depth: int = Field(default=2, ge=1, le=4)


class ReasoningResponse(BaseModel):
    answer: str
    paths: list[GraphPath] = Field(default_factory=list)
    related: GraphNeighborhood | None = None
    confidence: float = 0.7

