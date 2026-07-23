from __future__ import annotations

import re

from app.schemas.business_graph import ReasoningRequest, ReasoningResponse
from app.services.graph_builder import GraphBuilder, graph_builder
from app.services.impact_analyzer import ImpactAnalyzer, impact_analyzer
from app.services.root_cause_engine import RootCauseEngine, root_cause_engine
from app.services.timeline_builder import TimelineBuilder, timeline_builder
from app.services.traversal_engine import TraversalEngine, traversal_engine


class ReasoningEngine:
    def __init__(
        self,
        builder: GraphBuilder | None = None,
        traversal: TraversalEngine | None = None,
        impact: ImpactAnalyzer | None = None,
        root_cause: RootCauseEngine | None = None,
        timeline: TimelineBuilder | None = None,
    ) -> None:
        self.builder = builder or graph_builder
        self.traversal = traversal or traversal_engine
        self.impact = impact or impact_analyzer
        self.root_cause = root_cause or root_cause_engine
        self.timeline = timeline or timeline_builder

    async def answer(self, request: ReasoningRequest, cookies: dict | None = None) -> ReasoningResponse:
        if not request.doctype or not request.name:
            return ReasoningResponse(answer="Please specify the document type and document name so I can inspect the business graph.", confidence=0.2)
        graph = await self.builder.neighborhood(request.doctype, request.name, depth=request.depth, cookies=cookies)
        text = request.question.lower()
        if any(term in text for term in ("impact", "affected", "cancel", "stop")):
            return self.impact.analyze(graph, action="impact analysis")
        if any(term in text for term in ("why", "root cause", "blocking", "blocked", "delayed", "can't", "cannot")):
            return self.root_cause.explain(graph, request.question)
        target = self._target_doctype(request.question)
        if target:
            path = self.traversal.shortest_path(graph, target)
            if path:
                return ReasoningResponse(answer=f"I found a relationship path: {path.explanation}.", paths=[path], related=graph, confidence=0.78)
        count = len(graph.nodes) - 1
        return ReasoningResponse(answer=f"I found {count} document{'s' if count != 1 else ''} connected to {request.doctype} {request.name}.", related=graph, confidence=0.7)

    @staticmethod
    def _target_doctype(question: str) -> str | None:
        text = question.lower()
        candidates = {
            "supplier": "Supplier",
            "customer": "Customer",
            "invoice": "Sales Invoice",
            "purchase invoice": "Purchase Invoice",
            "payment": "Payment Entry",
            "ledger": "GL Entry",
            "task": "Task",
            "project": "Project",
            "warehouse": "Warehouse",
            "item": "Item",
        }
        for phrase, doctype in sorted(candidates.items(), key=lambda item: len(item[0]), reverse=True):
            if re.search(rf"\b{re.escape(phrase)}\b", text):
                return doctype
        return None


reasoning_engine = ReasoningEngine()

