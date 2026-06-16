"""Passive typed graph abstraction for ARC object relations."""

from __future__ import annotations

from collections import deque
from typing import Any, Iterable, Mapping

from core.math_reasoning.spatial_relations import SpatialRelationsEngine, normalize_object


Graph = dict[str, Any]
Node = dict[str, Any]
Edge = dict[str, Any]


class GraphRelationsEngine:
    """Represent ARC objects as nodes and spatial relations as typed edges."""

    system_name = "graph_relations_engine"

    def build_graph(
        self,
        objects: Iterable[Mapping[str, Any]],
        spatial_report: Mapping[str, Any] | None = None,
    ) -> Graph:
        normalized = [
            normalize_object(obj, fallback_id=f"object_{index + 1}")
            for index, obj in enumerate(objects)
        ]
        if spatial_report is None:
            spatial_report = SpatialRelationsEngine().analyze(normalized)

        graph: Graph = {
            "system": self.system_name,
            "node_count": 0,
            "edge_count": 0,
            "nodes": [],
            "edges": [],
            "graph_signature": {},
        }
        for object_item in normalized:
            self.add_node(graph, object_item)
        for relation in spatial_report.get("relations", []):
            source = relation.get("source")
            target = relation.get("target")
            relation_name = relation.get("relation")
            if source is None or target is None or relation_name is None:
                continue
            if source not in self._node_ids(graph) or target not in self._node_ids(graph):
                continue
            self.add_edge(
                graph,
                str(source),
                str(target),
                str(relation_name),
                weight=float(relation.get("confidence", relation.get("weight", 1.0))),
                directed=bool(relation.get("directed", True)),
            )
        self._refresh_counts(graph)
        graph["graph_signature"] = self.graph_signature(graph)
        return graph

    def add_node(self, graph: Graph, object_item: Mapping[str, Any]) -> Graph:
        obj = normalize_object(object_item)
        node_id = obj["id"]
        existing = self._node_by_id(graph, node_id)
        attributes = {
            "color": obj.get("color"),
            "area": obj.get("area"),
            "bbox": dict(obj.get("bbox", {})),
            "center": list(obj.get("center", [])),
        }
        if existing is None:
            graph.setdefault("nodes", []).append({"id": node_id, "attributes": attributes})
        else:
            existing["attributes"] = attributes
        self._refresh_counts(graph)
        return graph

    def add_edge(
        self,
        graph: Graph,
        source: str,
        target: str,
        relation: str,
        weight: float = 1.0,
        directed: bool = True,
    ) -> Graph:
        edge = {
            "source": str(source),
            "target": str(target),
            "relation": str(relation),
            "weight": round(float(weight), 4),
            "directed": bool(directed),
        }
        if self._edge_key(edge) not in {self._edge_key(item) for item in graph.setdefault("edges", [])}:
            graph["edges"].append(edge)
        self._refresh_counts(graph)
        return graph

    def neighbors(self, graph: Graph, node_id: str) -> list[str]:
        neighbors = set()
        for edge in graph.get("edges", []):
            if edge["source"] == node_id:
                neighbors.add(edge["target"])
            if edge["target"] == node_id:
                neighbors.add(edge["source"])
        return sorted(neighbors)

    def degree(self, graph: Graph, node_id: str) -> int:
        return len(self.neighbors(graph, node_id))

    def connected_components(self, graph: Graph) -> list[list[str]]:
        node_ids = sorted(self._node_ids(graph))
        unvisited = set(node_ids)
        components: list[list[str]] = []
        while unvisited:
            start = min(unvisited)
            queue: deque[str] = deque([start])
            component = []
            unvisited.remove(start)
            while queue:
                node_id = queue.popleft()
                component.append(node_id)
                for neighbor in self.neighbors(graph, node_id):
                    if neighbor in unvisited:
                        unvisited.remove(neighbor)
                        queue.append(neighbor)
            components.append(sorted(component))
        return components

    def shortest_path(self, graph: Graph, source: str, target: str) -> list[str]:
        source = str(source)
        target = str(target)
        if source == target and source in self._node_ids(graph):
            return [source]
        queue: deque[tuple[str, list[str]]] = deque([(source, [source])])
        visited = {source}
        while queue:
            node_id, path = queue.popleft()
            for neighbor in self._out_neighbors(graph, node_id):
                if neighbor in visited:
                    continue
                next_path = path + [neighbor]
                if neighbor == target:
                    return next_path
                visited.add(neighbor)
                queue.append((neighbor, next_path))
        return []

    def relation_path(self, graph: Graph, source: str, target: str) -> list[dict[str, str]]:
        path = self.shortest_path(graph, source, target)
        if len(path) < 2:
            return []
        relation_path = []
        for index in range(len(path) - 1):
            edge = self._first_edge_between(graph, path[index], path[index + 1])
            if edge:
                relation_path.append(
                    {
                        "source": edge["source"],
                        "target": edge["target"],
                        "relation": edge["relation"],
                    }
                )
        return relation_path

    def relation_types(self, graph: Graph) -> list[str]:
        return sorted({str(edge["relation"]) for edge in graph.get("edges", [])})

    def degree_distribution(self, graph: Graph) -> dict[str, int]:
        distribution: dict[str, int] = {}
        for node in sorted(graph.get("nodes", []), key=lambda item: item["id"]):
            degree = str(self.degree(graph, node["id"]))
            distribution[degree] = distribution.get(degree, 0) + 1
        return distribution

    def graph_signature(self, graph: Graph) -> dict[str, Any]:
        return {
            "connected_components": len(self.connected_components(graph)),
            "degree_distribution": self.degree_distribution(graph),
            "relation_types": self.relation_types(graph),
        }

    def compare_graphs(self, graph_a: Graph, graph_b: Graph) -> dict[str, Any]:
        nodes_a = self._node_ids(graph_a)
        nodes_b = self._node_ids(graph_b)
        edges_a = self._edge_keys(graph_a)
        edges_b = self._edge_keys(graph_b)
        comparison = {
            "node_count_change": len(nodes_b) - len(nodes_a),
            "edge_count_change": len(edges_b) - len(edges_a),
            "preserved_nodes": sorted(nodes_a & nodes_b),
            "added_nodes": sorted(nodes_b - nodes_a),
            "removed_nodes": sorted(nodes_a - nodes_b),
            "preserved_edges": self._edge_records(edges_a & edges_b),
            "added_edges": self._edge_records(edges_b - edges_a),
            "removed_edges": self._edge_records(edges_a - edges_b),
            "changed_relations": self.detect_relation_change(graph_a, graph_b),
            "structural_similarity": self._structural_similarity(nodes_a, nodes_b, edges_a, edges_b),
        }
        return {"system": self.system_name, "comparison": comparison}

    def detect_graph_growth(self, graph_a: Graph, graph_b: Graph) -> dict[str, Any]:
        comparison = self.compare_graphs(graph_a, graph_b)["comparison"]
        return {
            "node_growth": comparison["node_count_change"],
            "edge_growth": comparison["edge_count_change"],
            "added_nodes": comparison["added_nodes"],
            "added_edges": comparison["added_edges"],
            "grew": comparison["node_count_change"] > 0 or comparison["edge_count_change"] > 0,
        }

    def detect_graph_preservation(self, graph_a: Graph, graph_b: Graph) -> dict[str, Any]:
        comparison = self.compare_graphs(graph_a, graph_b)["comparison"]
        original_nodes = max(1, len(self._node_ids(graph_a)))
        original_edges = max(1, len(self._edge_keys(graph_a)))
        return {
            "preserved_nodes": comparison["preserved_nodes"],
            "preserved_edges": comparison["preserved_edges"],
            "node_preservation_ratio": round(len(comparison["preserved_nodes"]) / original_nodes, 4),
            "edge_preservation_ratio": round(len(comparison["preserved_edges"]) / original_edges, 4),
        }

    def detect_relation_change(self, graph_a: Graph, graph_b: Graph) -> list[dict[str, Any]]:
        relations_a = self._relations_by_pair(graph_a)
        relations_b = self._relations_by_pair(graph_b)
        changes = []
        for pair in sorted(set(relations_a) & set(relations_b)):
            removed = sorted(relations_a[pair] - relations_b[pair])
            added = sorted(relations_b[pair] - relations_a[pair])
            if removed or added:
                changes.append(
                    {
                        "source": pair[0],
                        "target": pair[1],
                        "from_relations": sorted(relations_a[pair]),
                        "to_relations": sorted(relations_b[pair]),
                        "removed_relations": removed,
                        "added_relations": added,
                    }
                )
        return changes

    def _refresh_counts(self, graph: Graph) -> None:
        graph["node_count"] = len(graph.get("nodes", []))
        graph["edge_count"] = len(graph.get("edges", []))

    def _node_by_id(self, graph: Graph, node_id: str) -> Node | None:
        for node in graph.get("nodes", []):
            if node.get("id") == node_id:
                return node
        return None

    def _node_ids(self, graph: Graph) -> set[str]:
        return {str(node["id"]) for node in graph.get("nodes", [])}

    def _out_neighbors(self, graph: Graph, node_id: str) -> list[str]:
        neighbors = []
        for edge in graph.get("edges", []):
            if edge["source"] == node_id:
                neighbors.append(edge["target"])
            if not edge.get("directed", True) and edge["target"] == node_id:
                neighbors.append(edge["source"])
        return sorted(set(neighbors))

    def _first_edge_between(self, graph: Graph, source: str, target: str) -> Edge | None:
        for edge in sorted(graph.get("edges", []), key=self._edge_key):
            if edge["source"] == source and edge["target"] == target:
                return edge
            if not edge.get("directed", True) and edge["source"] == target and edge["target"] == source:
                return edge
        return None

    def _edge_key(self, edge: Mapping[str, Any]) -> tuple[str, str, str, bool]:
        return (
            str(edge["source"]),
            str(edge["target"]),
            str(edge["relation"]),
            bool(edge.get("directed", True)),
        )

    def _edge_keys(self, graph: Graph) -> set[tuple[str, str, str, bool]]:
        return {self._edge_key(edge) for edge in graph.get("edges", [])}

    def _edge_records(self, edge_keys: Iterable[tuple[str, str, str, bool]]) -> list[Edge]:
        return [
            {
                "source": source,
                "target": target,
                "relation": relation,
                "directed": directed,
            }
            for source, target, relation, directed in sorted(edge_keys)
        ]

    def _relations_by_pair(self, graph: Graph) -> dict[tuple[str, str], set[str]]:
        relation_map: dict[tuple[str, str], set[str]] = {}
        for edge in graph.get("edges", []):
            pair = (str(edge["source"]), str(edge["target"]))
            relation_map.setdefault(pair, set()).add(str(edge["relation"]))
        return relation_map

    def _structural_similarity(
        self,
        nodes_a: set[str],
        nodes_b: set[str],
        edges_a: set[tuple[str, str, str, bool]],
        edges_b: set[tuple[str, str, str, bool]],
    ) -> float:
        node_similarity = self._jaccard(nodes_a, nodes_b)
        edge_similarity = self._jaccard(edges_a, edges_b)
        return round((node_similarity + edge_similarity) / 2.0, 4)

    def _jaccard(self, first: set[Any], second: set[Any]) -> float:
        if not first and not second:
            return 1.0
        return len(first & second) / len(first | second)


__all__ = ["GraphRelationsEngine"]
