from __future__ import annotations

from collections import deque

from app.schemas.business_graph import GraphNeighborhood, GraphPath


class TraversalEngine:
    def connected_documents(self, graph: GraphNeighborhood) -> GraphNeighborhood:
        return graph

    def shortest_path(self, graph: GraphNeighborhood, target_doctype: str, target_name: str | None = None) -> GraphPath | None:
        adjacency: dict[str, list[tuple[str, object]]] = {}
        for edge in graph.edges:
            adjacency.setdefault(edge.source_id, []).append((edge.target_id, edge))
        nodes = {node.id: node for node in graph.nodes}
        queue = deque([(graph.root.id, [], [])])
        visited = {graph.root.id}
        while queue:
            node_id, path_nodes, path_edges = queue.popleft()
            node = nodes[node_id]
            current_nodes = [*path_nodes, node]
            if node.doctype == target_doctype and (not target_name or node.name == target_name):
                return GraphPath(nodes=current_nodes, edges=path_edges, explanation=" → ".join(f"{item.doctype} {item.name}" for item in current_nodes))
            for next_id, edge in adjacency.get(node_id, []):
                if next_id not in visited and next_id in nodes:
                    visited.add(next_id)
                    queue.append((next_id, current_nodes, [*path_edges, edge]))
        return None


traversal_engine = TraversalEngine()
