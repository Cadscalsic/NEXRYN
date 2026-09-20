"""Validation for structured dependency graphs."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.dependency.dependency_graph_builder import EDGE_TYPES, NODE_FAMILIES


class DependencyGraphValidator:
    """Validate graph connectivity, consistency, cycles, and transitions."""

    system_name = "dependency_graph_validator"

    def validate(self, graph: Mapping[str, Any] | None = None) -> dict[str, Any]:
        graph = graph if isinstance(graph, Mapping) else {}
        nodes = {
            str(node.get("id"))
            for node in graph.get("nodes", []) or []
            if isinstance(node, Mapping) and node.get("id") is not None
        }
        node_types = {
            str(node.get("id")): str(
                node.get("node_family")
                or node.get("node_type")
                or node.get("type")
                or ""
            )
            for node in graph.get("nodes", []) or []
            if isinstance(node, Mapping) and node.get("id") is not None
        }
        connected = set()
        broken_chains = []
        invalid_transitions = []
        for edge in graph.get("edges", []) or []:
            if not isinstance(edge, Mapping):
                continue
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            relation = str(edge.get("relationship") or edge.get("edge_type") or edge.get("relation"))
            if source not in nodes or target not in nodes:
                broken_chains.append({
                    "source": source,
                    "target": target,
                    "reason": "edge_references_missing_node",
                })
            else:
                connected.update([source, target])
            if relation not in EDGE_TYPES:
                invalid_transitions.append({
                    "source": source,
                    "target": target,
                    "relationship": relation,
                    "reason": "unsupported_dependency_relationship",
                })
        invalid_nodes = [
            {"node_id": node_id, "node_family": family}
            for node_id, family in node_types.items()
            if family not in NODE_FAMILIES
        ]
        root_ids = {
            str(concept).lower() + ":" + str(concept).lower()
            for concept in graph.get("root_concepts", []) or []
        }
        orphan_nodes = sorted(nodes - connected - root_ids)
        cycle_count = self._cycle_count(graph)
        missing_prerequisites = self._missing_prerequisites(graph, nodes)
        graph_failures = (
            len(broken_chains)
            + len(invalid_transitions)
            + len(invalid_nodes)
            + len(orphan_nodes)
            + cycle_count
            + len(missing_prerequisites)
        )
        denominator = max(
            len(nodes) + len(graph.get("edges", []) or []),
            1,
        )
        validation_score = round(max(0.0, 1.0 - graph_failures / denominator), 4)
        return {
            "system": self.system_name,
            "graph_connectivity_valid": not orphan_nodes and not broken_chains,
            "graph_consistency_valid": not invalid_nodes and not invalid_transitions,
            "cycle_detection_passed": cycle_count == 0,
            "cycle_count": cycle_count,
            "orphan_nodes": orphan_nodes,
            "broken_chains": broken_chains,
            "missing_prerequisites": missing_prerequisites,
            "invalid_transitions": invalid_transitions,
            "invalid_nodes": invalid_nodes,
            "graph_failures": graph_failures,
            "validation_score": validation_score,
            "timestamp": str(datetime.utcnow()),
        }

    def _cycle_count(self, graph: Mapping[str, Any]) -> int:
        adjacency: dict[str, list[str]] = {}
        for edge in graph.get("edges", []) or []:
            if isinstance(edge, Mapping):
                adjacency.setdefault(str(edge.get("source")), []).append(
                    str(edge.get("target"))
                )
        cycles = 0
        visiting = set()
        visited = set()

        def visit(node_id: str) -> None:
            nonlocal cycles
            if node_id in visiting:
                cycles += 1
                return
            if node_id in visited:
                return
            visiting.add(node_id)
            for child in adjacency.get(node_id, []):
                visit(child)
            visiting.remove(node_id)
            visited.add(node_id)

        for node in graph.get("nodes", []) or []:
            if isinstance(node, Mapping) and node.get("id") is not None:
                visit(str(node.get("id")))
        return cycles

    def _missing_prerequisites(
        self,
        graph: Mapping[str, Any],
        nodes: set[str],
    ) -> list[dict[str, str]]:
        missing = []
        incoming = set()
        for edge in graph.get("edges", []) or []:
            if isinstance(edge, Mapping) and edge.get("target") is not None:
                incoming.add(str(edge.get("target")))
        for edge in graph.get("edges", []) or []:
            if not isinstance(edge, Mapping):
                continue
            relation = str(edge.get("relationship") or edge.get("edge_type") or edge.get("relation"))
            source = str(edge.get("source"))
            if relation in {"requires", "depends_on"} and source not in nodes:
                missing.append({
                    "node_id": source,
                    "reason": "required_source_node_missing",
                })
        root_ids = {
            str(concept).lower() + ":" + str(concept).lower()
            for concept in graph.get("root_concepts", []) or []
        }
        for node_id in nodes - incoming - root_ids:
            if ":start" not in node_id and ":initial" not in node_id:
                continue
            missing.append({
                "node_id": node_id,
                "reason": "initial_node_has_no_explicit_prerequisite",
            })
        return missing


dependency_graph_validator = DependencyGraphValidator()


__all__ = ["DependencyGraphValidator", "dependency_graph_validator"]
