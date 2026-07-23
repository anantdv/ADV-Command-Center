from __future__ import annotations

from app.schemas.business_graph import GraphNeighborhood, ReasoningResponse


class ImpactAnalyzer:
    def analyze(self, graph: GraphNeighborhood, action: str = "change") -> ReasoningResponse:
        affected = [node for node in graph.nodes if node.id != graph.root.id]
        count = len(affected)
        names = ", ".join(f"{node.doctype} {node.name}" for node in affected[:8])
        suffix = f" Affected documents include {names}." if names else ""
        return ReasoningResponse(answer=f"{action.title()} on {graph.root.doctype} {graph.root.name} may affect {count} connected document{'s' if count != 1 else ''}.{suffix}", related=graph, confidence=0.74)


impact_analyzer = ImpactAnalyzer()

