from collections import defaultdict, deque

from core.causal.causal_edge import CausalEdge
from core.causal.causal_node import CausalNode


class CausalGraph:
    """Small explicit causal graph for concepts, contexts, and outcomes."""

    def __init__(self):
        self.nodes = {}
        self.edges = []
        self._edge_index = {}

    def add_node(
        self,
        node=None,
        node_id=None,
        node_type="concept",
        name=None,
        confidence=0.0,
        support_score=0.0,
        contradiction_score=0.0,
        metadata=None,
        evidence_count=0,
        timestamp="",
    ):
        if node is None:
            node = CausalNode(
                node_id=node_id,
                node_type=node_type,
                name=name or node_id,
                confidence=confidence,
                support_score=support_score,
                contradiction_score=contradiction_score,
                metadata=metadata or {},
                evidence_count=evidence_count,
                timestamp=timestamp,
            )
        elif isinstance(node, dict):
            node = CausalNode(**node)

        if node.node_id in self.nodes:
            return self.nodes[node.node_id].merge(node)
        self.nodes[node.node_id] = node
        return node

    def remove_node(self, node_id):
        node = self.nodes.pop(node_id, None)
        if node is None:
            return None
        self.edges = [
            edge
            for edge in self.edges
            if edge.source != node_id and edge.target != node_id
        ]
        self._rebuild_edge_index()
        return node

    def add_edge(
        self,
        edge=None,
        source=None,
        target=None,
        relation_type="supports",
        weight=1.0,
        confidence=0.0,
        evidence=None,
        timestamp="",
    ):
        if edge is None:
            edge = CausalEdge(
                source=source,
                target=target,
                relation_type=relation_type,
                weight=weight,
                confidence=confidence,
                evidence=evidence or [],
                timestamp=timestamp,
            )
        elif isinstance(edge, dict):
            edge = CausalEdge(**edge)

        key = (edge.source, edge.target, edge.relation_type)
        if key in self._edge_index:
            return self.edges[self._edge_index[key]].merge(edge)
        self._edge_index[key] = len(self.edges)
        self.edges.append(edge)
        return edge

    def remove_edge(self, source, target, relation_type=None):
        removed = []
        retained = []
        for edge in self.edges:
            matches = (
                edge.source == source
                and edge.target == target
                and (
                    relation_type is None
                    or edge.relation_type == relation_type
                )
            )
            if matches:
                removed.append(edge)
            else:
                retained.append(edge)
        self.edges = retained
        self._rebuild_edge_index()
        return removed

    def _rebuild_edge_index(self):
        self._edge_index = {
            (edge.source, edge.target, edge.relation_type): index
            for index, edge in enumerate(self.edges)
        }

    def ensure_concept(self, concept, confidence=0.0, metadata=None):
        return self.add_node(
            node_id=f"concept:{concept}",
            node_type="concept",
            name=concept,
            confidence=confidence,
            metadata=metadata or {},
        )

    def ensure_context(self, key, value, confidence=1.0):
        context_id = f"context:{key}:{value}"
        return self.add_node(
            node_id=context_id,
            node_type="context",
            name=f"{key}={value}",
            confidence=confidence,
            metadata={"context_key": key, "context_value": value},
        )

    def ensure_outcome(self, concept, confidence=0.0):
        return self.add_node(
            node_id=f"outcome:{concept}",
            node_type="truth",
            name=f"{concept} accepted",
            confidence=confidence,
        )

    def adjacency(self, reverse=False):
        adjacency = defaultdict(list)
        for edge in self.edges:
            source = edge.target if reverse else edge.source
            target = edge.source if reverse else edge.target
            adjacency[source].append((target, edge))
        return adjacency

    def incoming(self, node_id, relation_type=None):
        return [
            edge
            for _source, edge in self.adjacency(reverse=True).get(node_id, [])
            if relation_type is None or edge.relation_type == relation_type
        ]

    def outgoing(self, node_id, relation_type=None):
        return [
            edge
            for _target, edge in self.adjacency().get(node_id, [])
            if relation_type is None or edge.relation_type == relation_type
        ]

    def find_path(self, source, target=None, relation_types=None):
        allowed = set(relation_types or [])
        queue = deque([(source, [source])])
        visited = set()
        while queue:
            node_id, path = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)
            if target is not None and node_id == target and len(path) > 1:
                return path
            for next_id, edge in self.adjacency().get(node_id, []):
                if allowed and edge.relation_type not in allowed:
                    continue
                queue.append((next_id, [*path, next_id]))
        return []

    def find_all_paths(
        self,
        source,
        target=None,
        max_depth=6,
        relation_types=None,
    ):
        allowed = set(relation_types or [])
        paths = []
        queue = deque([(source, [source], [])])
        while queue:
            node_id, path, path_edges = queue.popleft()
            if len(path) > max_depth + 1:
                continue
            if target is not None and node_id == target and len(path) > 1:
                paths.append((path, path_edges))
                continue
            for next_id, edge in self.adjacency().get(node_id, []):
                if next_id in path:
                    continue
                if allowed and edge.relation_type not in allowed:
                    continue
                queue.append((next_id, [*path, next_id], [*path_edges, edge]))
        return paths

    def find_dependencies(self, node_id):
        return [
            {
                "node": self.nodes.get(edge.source).as_dict(),
                "edge": edge.as_dict(),
            }
            for edge in self.incoming(node_id)
            if edge.source in self.nodes
            and edge.relation_type in {
                "depends_on",
                "supports",
                "context_requires",
                "context_strengthens",
                "context_weakens",
            }
        ]

    def find_dependents(self, node_id):
        return [
            {
                "node": self.nodes.get(edge.target).as_dict(),
                "edge": edge.as_dict(),
            }
            for edge in self.outgoing(node_id)
            if edge.target in self.nodes
        ]

    def find_root_causes(self, node_id):
        reverse = self.adjacency(reverse=True)
        roots = set()
        queue = deque([node_id])
        visited = set()
        causal_relations = {
            "causes",
            "supports",
            "enables",
            "explains",
            "depends_on",
            "context_requires",
            "invalidates",
            "implies",
        }
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            parents = [
                source
                for source, edge in reverse.get(current, [])
                if edge.relation_type in causal_relations
            ]
            if not parents and current != node_id:
                roots.add(current)
            for parent in parents:
                queue.append(parent)
        return [
            self.nodes[item].as_dict()
            for item in sorted(roots)
            if item in self.nodes
        ]

    def find_leaf_effects(self, node_id):
        leaves = set()
        queue = deque([node_id])
        visited = set()
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            children = [
                target
                for target, edge in self.adjacency().get(current, [])
                if edge.relation_type in {
                    "causes",
                    "supports",
                    "enables",
                    "explains",
                    "implies",
                    "invalidates",
                }
            ]
            if not children and current != node_id:
                leaves.add(current)
            for child in children:
                queue.append(child)
        return [
            self.nodes[item].as_dict()
            for item in sorted(leaves)
            if item in self.nodes
        ]

    def detect_cycles(self):
        adjacency = self.adjacency()
        cycles = []
        visited = set()
        active = set()

        def visit(node_id, path):
            if node_id in active:
                cycles.append(path[path.index(node_id):])
                return
            if node_id in visited:
                return
            visited.add(node_id)
            active.add(node_id)
            for target, _edge in adjacency.get(node_id, []):
                visit(target, [*path, target])
            active.remove(node_id)

        for node_id in self.nodes:
            visit(node_id, [node_id])
        return cycles

    def compute_graph_strength(self):
        if not self.edges:
            return 0.0
        return round(
            sum(
                (edge.weight + edge.confidence) / 2.0
                for edge in self.edges
            )
            / len(self.edges),
            4,
        )

    def concept_path_complete(self, concept):
        concept_id = f"concept:{concept}"
        outcome_id = f"outcome:{concept}"
        path = self.find_path(
            concept_id,
            outcome_id,
            relation_types=["supports", "explains", "causes", "enables"],
        )
        return bool(path), path

    def export_graph(self):
        return {
            "nodes": [node.as_dict() for node in self.nodes.values()],
            "edges": [edge.as_dict() for edge in self.edges],
        }


__all__ = [
    "CausalGraph",
]
