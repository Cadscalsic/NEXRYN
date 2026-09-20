"""Evaluate contextual truth support from registered contexts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.context.context_validator import validate_context_collection


class ContextualTruthEngine:
    """Expose context support as a direct promotion input."""

    system_name = "contextual_truth_engine"

    def evaluate(
        self,
        concept: str,
        contexts: Iterable[Mapping[str, Any]] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        contexts, context_telemetry = validate_context_collection(contexts)
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        matching = [
            context
            for context in contexts
            if str(context.get("concept") or "") == str(concept or "")
        ] or contexts
        confidence = _average(context.get("confidence", 0.0) for context in matching)
        dependencies = []
        constraints = []
        boundaries = []
        for context in matching:
            dependency_chain = context.get("dependency_chain", [])
            if isinstance(dependency_chain, list):
                dependencies.extend(dependency_chain[:6])
            identity = context.get("identity_constraints", {})
            if isinstance(identity, Mapping):
                constraints.extend(str(key) for key in identity.keys())
            if context.get("context_type"):
                boundaries.append(str(context["context_type"]))

        return {
            "system": self.system_name,
            "report_state": "final",
            "concept": str(concept or "runtime_concept"),
            "contextual_truth_supported": confidence >= 0.60,
            "contextual_truth_confidence": round(confidence, 4),
            "contextual_truth_dependencies": _unique(dependencies),
            "contextual_truth_constraints": _unique(constraints),
            "contextual_truth_boundaries": _unique(boundaries),
            "result_count": len(matching),
            **context_telemetry,
            "reason": None if matching else "no_registered_contexts",
        }


def _average(values: Iterable[Any]) -> float:
    numbers = []
    for value in values:
        try:
            numbers.append(max(0.0, min(1.0, float(value))))
        except (TypeError, ValueError):
            continue
    return round(sum(numbers) / len(numbers), 4) if numbers else 0.0


def _unique(values: Iterable[Any]) -> list[Any]:
    result = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


contextual_truth_engine = ContextualTruthEngine()


__all__ = ["ContextualTruthEngine", "contextual_truth_engine"]
