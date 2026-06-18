"""Generate human-readable explanatory dependency paths."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from core.epistemic_models import clamp


class ExplanationEngine:
    system_name = "explanation_engine"

    def explain(
        self,
        concept: str,
        chain_edges: Iterable[Mapping[str, Any]],
        dependency_graph: Mapping[str, Any],
    ) -> dict[str, Any]:
        path = [
            {
                "from": edge.get("source"),
                "dependency_type": edge.get("dependency_type"),
                "to": edge.get("target"),
                "confidence": edge.get("confidence", 0.0),
                "why": (
                    f"{edge.get('source')} {edge.get('dependency_type')} "
                    f"{edge.get('target')}"
                ),
            }
            for edge in chain_edges
        ]
        graph_nodes = dependency_graph.get("nodes", [])
        graph_edges = dependency_graph.get("edges", [])
        explanation_quality = clamp(
            min(len(path) / 4.0, 1.0) * 0.42
            + min(len(graph_edges) / max(len(graph_nodes), 1), 1.0) * 0.20
            + (
                sum(clamp(item.get("confidence", 0.0)) for item in path)
                / len(path)
                if path
                else 0.0
            )
            * 0.28
            + (0.10 if graph_nodes and graph_edges else 0.0)
        )
        return {
            "system": self.system_name,
            "concept": concept,
            "explanation_path": path,
            "explanation_quality": round(explanation_quality, 4),
            "dependency_explanation_quality": round(explanation_quality, 4),
            "explanation_path_generated": bool(path),
        }


__all__ = ["ExplanationEngine"]
