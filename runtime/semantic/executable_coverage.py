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
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        normalized = list(dict.fromkeys(_normalize(item) for item in concepts or [] if _normalize(item)))
        if not normalized:
            lifecycle_concepts = _collect_context_concepts(runtime_context)
            if lifecycle_concepts:
                return {
                    "system": self.system_name,
                    "total_concepts": 0,
                    "semantic_concepts_observed": len(lifecycle_concepts),
                    "executable_concepts": 0,
                    "coverage_percentage": None,
                    "coverage_state": "NOT_MEASURABLE",
                    "measurement_blocker": "NO_EXECUTABLE_CONCEPT_INPUT",
                    "lifecycle_concepts": lifecycle_concepts,
                    "unsupported_concepts": [],
                    "missing_primitives": [],
                    "unsupported_execution_routes": [],
                    "concept_evaluations": [],
                }
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
            "semantic_concepts_observed": total,
            "executable_concepts": len(executable),
            "coverage_percentage": round(coverage, 2),
            "coverage_state": "MEASURED",
            "measurement_blocker": None,
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


def _collect_context_concepts(runtime_context: Mapping[str, Any]) -> list[str]:
    concepts: list[str] = []

    def add(value: Any) -> None:
        token = _normalize(value)
        if token:
            concepts.append(token)

    def visit(value: Any) -> None:
        if isinstance(value, str):
            add(value)
            return
        if isinstance(value, Mapping):
            for key, item in value.items():
                if key in {
                    "concept",
                    "concepts",
                    "detected_concepts",
                    "attributed_concepts",
                    "semantic_concepts",
                    "generated_concepts",
                    "target_concepts",
                    "matched_concepts",
                    "routed_concepts",
                }:
                    visit(item)
                elif key in {
                    "concept_lifecycle_report",
                    "semantic_attribution_report",
                    "semantic_compilation_report",
                    "truth_candidate_report",
                    "truth_candidate_engine_report",
                }:
                    visit(item)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                visit(item)

    visit(runtime_context)
    return list(dict.fromkeys(concepts))


executable_coverage = ExecutableCoverageTracker()

__all__ = [
    "ExecutableCoverageTracker",
    "executable_coverage",
]
