"""Registry for dependency runtime outputs and execution lineage."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Mapping


class DependencyOutputRegistry:
    """Store generated chains, confidence, outputs, and lineage."""

    system_name = "dependency_output_registry"

    def __init__(self):
        self.outputs: list[dict[str, Any]] = []

    def register(
        self,
        *,
        concept: str,
        chain: list[str],
        output: Mapping[str, Any] | None = None,
        confidence: float = 0.0,
        lineage: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        record = {
            "system": self.system_name,
            "concept": str(concept),
            "generated_chain": list(chain),
            "dependency_output": dict(output or {}),
            "dependency_confidence": round(float(confidence or 0.0), 4),
            "execution_lineage": dict(lineage or {}),
            "dependency_depth": max(len(chain) - 1, 0),
            "timestamp": str(datetime.utcnow()),
        }
        self.outputs.append(record)
        return deepcopy(record)

    def all_outputs(self) -> list[dict[str, Any]]:
        return deepcopy(self.outputs)

    def report(self) -> dict[str, Any]:
        depths = [int(item.get("dependency_depth", 0) or 0) for item in self.outputs]
        confidences = [
            float(item.get("dependency_confidence", 0.0) or 0.0)
            for item in self.outputs
        ]
        return {
            "system": self.system_name,
            "dependency_output_count": len(self.outputs),
            "generated_chains": [
                item.get("generated_chain", [])
                for item in self.outputs
            ],
            "dependency_outputs": self.all_outputs(),
            "dependency_confidence": (
                round(sum(confidences) / len(confidences), 4)
                if confidences
                else 0.0
            ),
            "dependency_depth": max(depths or [0]),
            "execution_lineage": [
                item.get("execution_lineage", {})
                for item in self.outputs
            ],
        }


dependency_output_registry = DependencyOutputRegistry()


__all__ = ["DependencyOutputRegistry", "dependency_output_registry"]
