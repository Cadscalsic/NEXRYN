"""Memory for reusable dependency graph structures."""

from __future__ import annotations

import copy
from datetime import datetime
from typing import Any, Mapping


class DependencyGraphMemory:
    """Store graph successes, failures, signatures, motifs, and reuse patterns."""

    system_name = "dependency_graph_memory"

    def __init__(self):
        self.successful_graphs: list[dict[str, Any]] = []
        self.failed_graphs: list[dict[str, Any]] = []
        self.graph_signatures: dict[str, dict[str, Any]] = {}
        self.graph_reuse_patterns: dict[str, int] = {}
        self.dependency_motifs: dict[str, list[dict[str, Any]]] = {}

    def build_signature(self, graph: Mapping[str, Any] | None = None) -> str:
        graph = graph if isinstance(graph, Mapping) else {}
        concepts = ",".join(str(item) for item in graph.get("root_concepts", []) or [])
        edges = []
        for edge in graph.get("edges", []) or []:
            if isinstance(edge, Mapping):
                edges.append(
                    ":".join([
                        str(edge.get("source")),
                        str(edge.get("relationship") or edge.get("edge_type") or edge.get("relation")),
                        str(edge.get("target")),
                    ])
                )
        return "|".join([concepts, *sorted(edges)]) or "empty_dependency_graph"

    def remember(
        self,
        graph: Mapping[str, Any],
        validation_report: Mapping[str, Any] | None = None,
        success: bool | None = None,
        evidence: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        validation_report = (
            validation_report
            if isinstance(validation_report, Mapping)
            else {}
        )
        if success is None:
            success = (
                float(validation_report.get("validation_score", 0.0) or 0.0) >= 0.80
                and int(validation_report.get("graph_failures", 0) or 0) == 0
            )
        signature = self.build_signature(graph)
        record = {
            "signature": signature,
            "dependency_graph": copy.deepcopy(dict(graph)),
            "validation_report": copy.deepcopy(dict(validation_report)),
            "success": bool(success),
            "evidence": copy.deepcopy(dict(evidence or {})),
            "timestamp": str(datetime.utcnow()),
        }
        target = self.successful_graphs if success else self.failed_graphs
        target.append(record)
        self.graph_signatures[signature] = record
        for concept in graph.get("root_concepts", []) or []:
            key = str(concept)
            self.dependency_motifs.setdefault(key, [])
            self.dependency_motifs[key].append(copy.deepcopy(dict(graph)))
        return record

    def retrieve_similar(
        self,
        concepts: list[str] | None = None,
        limit: int = 3,
    ) -> list[dict[str, Any]]:
        concept_set = {str(concept) for concept in concepts or []}
        matches = []
        for record in self.successful_graphs:
            graph = record.get("dependency_graph", {})
            roots = {str(concept) for concept in graph.get("root_concepts", []) or []}
            if not concept_set or concept_set.intersection(roots):
                matches.append(copy.deepcopy(record))
        return matches[-limit:]

    def reuse_best(
        self,
        concepts: list[str] | None = None,
    ) -> dict[str, Any] | None:
        matches = self.retrieve_similar(concepts, limit=1)
        if not matches:
            return None
        record = matches[-1]
        signature = record.get("signature", "")
        self.graph_reuse_patterns[signature] = (
            self.graph_reuse_patterns.get(signature, 0) + 1
        )
        return copy.deepcopy(record.get("dependency_graph", {}))

    def build_report(self) -> dict[str, Any]:
        reuse_total = sum(self.graph_reuse_patterns.values())
        return {
            "system": self.system_name,
            "successful_graphs": len(self.successful_graphs),
            "failed_graphs": len(self.failed_graphs),
            "known_graph_signatures": len(self.graph_signatures),
            "dependency_motif_count": sum(
                len(items)
                for items in self.dependency_motifs.values()
            ),
            "graph_reuse_patterns": dict(self.graph_reuse_patterns),
            "graph_reuse_count": reuse_total,
        }


dependency_graph_memory = DependencyGraphMemory()


__all__ = ["DependencyGraphMemory", "dependency_graph_memory"]
