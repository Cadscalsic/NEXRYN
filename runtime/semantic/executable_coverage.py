"""Coverage accounting for executable semantic concepts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.semantic.executable_semantics import ExecutableSemanticIntelligence


class ExecutableCoverageTracker:
    """Track which semantic concepts can be routed to executable primitives."""

    system_name = "executable_coverage"

    def __init__(self, executable_semantics: ExecutableSemanticIntelligence | None = None):
        self.executable_semantics = executable_semantics or ExecutableSemanticIntelligence()

    def evaluate(
        self,
        concepts: Iterable[Any] | None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        normalized = list(dict.fromkeys(_normalize(item) for item in concepts or [] if _normalize(item)))
        evaluations = [
            self.executable_semantics.evaluate(concept, runtime_context=runtime_context)
            for concept in normalized
        ]
        executable = [
            item["concept"] for item in evaluations
            if item.get("is_executable")
        ]
        unsupported = [
            item["concept"] for item in evaluations
            if not item.get("is_executable")
        ]
        missing = sorted({
            primitive
            for item in evaluations
            for primitive in item.get("missing_primitives", []) or []
        })
        total = len(normalized)
        coverage = (len(executable) / total * 100.0) if total else 0.0
        return {
            "system": self.system_name,
            "total_concepts": total,
            "executable_concepts": len(executable),
            "coverage_percentage": round(coverage, 2),
            "unsupported_concepts": unsupported,
            "missing_primitives": missing,
            "unsupported_execution_routes": [
                item["concept"] for item in evaluations
                if item.get("coverage_state") == "UNSUPPORTED_EXECUTION_ROUTE"
            ],
            "concept_evaluations": evaluations,
        }


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


executable_coverage = ExecutableCoverageTracker()

__all__ = [
    "ExecutableCoverageTracker",
    "executable_coverage",
]
