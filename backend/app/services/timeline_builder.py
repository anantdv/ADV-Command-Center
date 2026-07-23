from __future__ import annotations

from app.schemas.business_graph import BusinessTimeline, GraphNeighborhood, TimelineEvent


DATE_KEYS = ("posting_date", "transaction_date", "creation", "modified")


class TimelineBuilder:
    def build(self, graph: GraphNeighborhood) -> BusinessTimeline:
        events: list[TimelineEvent] = []
        for node in graph.nodes:
            event_date = next((str(node.metadata.get(key)) for key in DATE_KEYS if node.metadata.get(key)), None)
            events.append(TimelineEvent(id=f"evt_{node.id}", doctype=node.doctype, name=node.name, label=node.label or node.name, event_type=node.node_type.value, event_date=event_date, status=node.status, metadata=node.metadata))
        events.sort(key=lambda item: item.event_date or "")
        return BusinessTimeline(root=graph.root, events=events)


timeline_builder = TimelineBuilder()

