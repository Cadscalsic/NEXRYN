"""Infer dependency graph structures from runtime signals."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from runtime.dependency.dependency_graph_builder import DependencyGraphBuilder
from runtime.dependency.dependency_graph_validator import DependencyGraphValidator
from runtime.memory.dependency_graph_memory import DependencyGraphMemory


class DependencyGraphDiscovery:
    """Infer nodes, edges, chains, hierarchy, and graph confidence."""

    system_name = "dependency_graph_discovery"

    def __init__(
        self,
        builder: DependencyGraphBuilder | None = None,
        validator: DependencyGraphValidator | None = None,
        memory: DependencyGraphMemory | None = None,
    ):
        self.builder = builder or DependencyGraphBuilder()
        self.validator = validator or DependencyGraphValidator()
        self.memory = memory or DependencyGraphMemory()

    def discover(
        self,
        *,
        concepts: list[str] | None = None,
        dependency_outputs: list[Mapping[str, Any]] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        concepts = self._normalize_concepts(concepts or [])
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        dependency_outputs = list(dependency_outputs or [])
        reuse_graph = self.memory.reuse_best(concepts)
        build_report = self.builder.build(
            detected_concepts=concepts,
            runtime_context=runtime_context,
            dependency_outputs=dependency_outputs,
            reuse_graph=reuse_graph,
        )
        graph = build_report.get("dependency_graph", {})
        validation = self.validator.validate(graph)
        memory_record = self.memory.remember(
            graph,
            validation_report=validation,
            success=validation.get("graph_failures", 0) == 0,
            evidence={
                "concepts": concepts,
                "dependency_output_count": len(dependency_outputs),
                "discovery_system": self.system_name,
            },
        )
        hierarchy = self._hierarchy(graph)
        report = {
            "system": self.system_name,
            **build_report,
            "dependency_graph_validation": validation,
            "dependency_graph_memory_record": memory_record,
            "dependency_graph_memory_report": self.memory.build_report(),
            "dependency_hierarchy": hierarchy,
            "dependency_hierarchy_depth": len(hierarchy),
            "graph_reuse_hits": build_report.get("DEPENDENCY_GRAPH_REPORT", {}).get(
                "graph_reuse_hits",
                0,
            ),
            "timestamp": str(datetime.utcnow()),
        }
        report["DEPENDENCY_GRAPH_REPORT"] = {
            **build_report.get("DEPENDENCY_GRAPH_REPORT", {}),
            "graph_failures": validation.get("graph_failures", 0),
            "orphan_nodes": validation.get("orphan_nodes", []),
            "cycle_count": validation.get("cycle_count", 0),
        }
        report["dependency_graph_validation_score"] = validation.get(
            "validation_score",
            0.0,
        )
        report["dependency_graph_reuse_rate"] = (
            1.0 if report.get("graph_reuse_hits", 0) > 0 else 0.0
        )
        return report

    def _hierarchy(self, graph: Mapping[str, Any]) -> list[dict[str, Any]]:
        nodes = {
            str(node.get("id")): node
            for node in graph.get("nodes", []) or []
            if isinstance(node, Mapping)
        }
        children: dict[str, list[str]] = {}
        incoming = set()
        for edge in graph.get("edges", []) or []:
            if not isinstance(edge, Mapping):
                continue
            source = str(edge.get("source"))
            target = str(edge.get("target"))
            children.setdefault(source, []).append(target)
            incoming.add(target)
        roots = [node_id for node_id in nodes if node_id not in incoming]
        hierarchy = []

        def walk(node_id: str, depth: int, seen: set[str]) -> None:
            if node_id in seen:
                return
            node = nodes.get(node_id, {})
            hierarchy.append({
                "node_id": node_id,
                "label": node.get("label") or node.get("name"),
                "node_family": node.get("node_family") or node.get("type"),
                "depth": depth,
            })
            for child in children.get(node_id, []):
                walk(child, depth + 1, seen | {node_id})

        for root in roots:
            walk(root, 0, set())
        return hierarchy

    def _normalize_concepts(self, concepts):
        normalized = []
        for concept in concepts:
            token = str(concept).strip().lower().replace("-", "_").replace(" ", "_")
            if token and token not in normalized:
                normalized.append(token)
        return normalized


dependency_graph_discovery = DependencyGraphDiscovery()


__all__ = ["DependencyGraphDiscovery", "dependency_graph_discovery"]
