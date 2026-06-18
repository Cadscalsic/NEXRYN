"""Trace engine for executable dependency chains."""

from __future__ import annotations

from typing import Any, Iterable, Mapping


class DependencyTraceEngine:
    system_name = "dependency_trace_engine"

    def trace(self, concept: str, edges: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        steps = [
            {
                "source": edge.get("source"),
                "dependency_type": edge.get("dependency_type"),
                "target": edge.get("target"),
                "confidence": edge.get("confidence", 0.0),
            }
            for edge in edges
        ]
        return {
            "system": self.system_name,
            "concept": concept,
            "steps": steps,
            "trace_length": len(steps),
            "dependency_trace_generated": True,
            "explanation_path": steps,
        }


__all__ = ["DependencyTraceEngine"]
