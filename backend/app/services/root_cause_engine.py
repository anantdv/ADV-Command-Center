from __future__ import annotations

from app.schemas.business_graph import GraphNeighborhood, ReasoningResponse


BLOCKING_STATUSES = {"Draft", "Pending", "Pending Approval", "Overdue", "Stopped", "On Hold", "To Receive", "To Bill"}


class RootCauseEngine:
    def explain(self, graph: GraphNeighborhood, question: str = "") -> ReasoningResponse:
        blockers = [node for node in graph.nodes if node.status in BLOCKING_STATUSES]
        if not blockers:
            return ReasoningResponse(answer=f"I did not find an obvious blocking document connected to {graph.root.doctype} {graph.root.name}.", related=graph, confidence=0.55)
        chain = " → ".join(f"{node.doctype} {node.name} ({node.status})" for node in blockers[:6])
        return ReasoningResponse(answer=f"The likely blocking chain is: {chain}. Review the earliest pending document first.", related=graph, confidence=0.72)


root_cause_engine = RootCauseEngine()

