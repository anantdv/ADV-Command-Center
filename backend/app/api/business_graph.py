from __future__ import annotations

from fastapi import APIRouter, Request

from app.dependencies import CurrentUserDep, get_frappe_cookies
from app.schemas.business_graph import (
    BusinessTimeline,
    GraphNeighborhood,
    GraphTraversalRequest,
    ReasoningRequest,
    ReasoningResponse,
    RelatedDocumentsResponse,
)
from app.schemas.common import ApiResponse
from app.services.graph_builder import graph_builder
from app.services.impact_analyzer import impact_analyzer
from app.services.reasoning_engine import reasoning_engine
from app.services.related_document_resolver import related_document_resolver
from app.services.root_cause_engine import root_cause_engine
from app.services.timeline_builder import timeline_builder
from app.services.traversal_engine import traversal_engine

router = APIRouter(prefix="/business-graph", tags=["Business Graph"])


@router.get("/documents/{doctype}/{name}/related", response_model=ApiResponse[RelatedDocumentsResponse])
async def related_documents(
    doctype: str,
    name: str,
    request: Request,
    _: CurrentUserDep,
    depth: int = 1,
) -> ApiResponse[RelatedDocumentsResponse]:
    return ApiResponse(
        data=await related_document_resolver.related(
            doctype,
            name,
            depth=depth,
            cookies=get_frappe_cookies(request),
        )
    )


@router.get("/documents/{doctype}/{name}/timeline", response_model=ApiResponse[BusinessTimeline])
async def business_timeline(
    doctype: str,
    name: str,
    request: Request,
    _: CurrentUserDep,
    depth: int = 2,
) -> ApiResponse[BusinessTimeline]:
    graph = await graph_builder.neighborhood(doctype, name, depth=depth, cookies=get_frappe_cookies(request))
    return ApiResponse(data=timeline_builder.build(graph))


@router.post("/traverse", response_model=ApiResponse[GraphNeighborhood])
async def traverse(
    payload: GraphTraversalRequest,
    request: Request,
    _: CurrentUserDep,
) -> ApiResponse[GraphNeighborhood]:
    return ApiResponse(
        data=await graph_builder.neighborhood(
            payload.doctype,
            payload.name,
            depth=payload.depth,
            direction=payload.direction,
            limit=payload.limit,
            cookies=get_frappe_cookies(request),
        )
    )


@router.post("/reason", response_model=ApiResponse[ReasoningResponse])
async def reason(
    payload: ReasoningRequest,
    request: Request,
    _: CurrentUserDep,
) -> ApiResponse[ReasoningResponse]:
    return ApiResponse(data=await reasoning_engine.answer(payload, cookies=get_frappe_cookies(request)))


@router.post("/impact", response_model=ApiResponse[ReasoningResponse])
async def impact(
    payload: ReasoningRequest,
    request: Request,
    _: CurrentUserDep,
) -> ApiResponse[ReasoningResponse]:
    if not payload.doctype or not payload.name:
        return ApiResponse(data=ReasoningResponse(answer="Please specify a document type and document name.", confidence=0.2))
    graph = await graph_builder.neighborhood(payload.doctype, payload.name, depth=payload.depth, cookies=get_frappe_cookies(request))
    return ApiResponse(data=impact_analyzer.analyze(graph, action=payload.question or "impact analysis"))


@router.post("/root-cause", response_model=ApiResponse[ReasoningResponse])
async def root_cause(
    payload: ReasoningRequest,
    request: Request,
    _: CurrentUserDep,
) -> ApiResponse[ReasoningResponse]:
    if not payload.doctype or not payload.name:
        return ApiResponse(data=ReasoningResponse(answer="Please specify a document type and document name.", confidence=0.2))
    graph = await graph_builder.neighborhood(payload.doctype, payload.name, depth=payload.depth, cookies=get_frappe_cookies(request))
    return ApiResponse(data=root_cause_engine.explain(graph, payload.question))
