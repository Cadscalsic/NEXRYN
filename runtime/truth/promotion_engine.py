"""Promotion evaluation for context-backed concepts."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.context.context_validator import validate_context_collection


class PromotionEngine:
    """Score concepts for truth candidate promotion without nullable gates."""

    system_name = "promotion_engine"

    def evaluate(
        self,
        concept: str,
        dependency_report: Mapping[str, Any] | None = None,
        contexts: Iterable[Mapping[str, Any]] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        dependency_report = (
            dependency_report
            if isinstance(dependency_report, Mapping)
            else {}
        )
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        contexts, context_telemetry = validate_context_collection(contexts)
        dependency_score = max(
            _score(
                dependency_report,
                "dependency_confidence",
                "dependency_coherence",
                "dependency_coherence_average",
                default=0.0,
            ),
            _score(
                dependency_report,
                "dependency_chain_coverage",
                "coverage",
                default=0.0,
            ),
            min(1.0, float(dependency_report.get("dependency_chain_depth", 0)) / 4),
        )
        context_score = _average(context.get("confidence", 0.0) for context in contexts)
        stability_score = _average(
            context.get("stability_score", 0.0)
            for context in contexts
        )
        promotion_bonus = round(
            0.06 if dependency_score >= 0.80 and context_score >= 0.70 else 0.0,
            4,
        )
        contradiction = _score(runtime_context, "contradiction_score", default=0.0)
        promotion_penalty = round(contradiction * 0.30, 4)
        promotion_score = round(
            max(
                0.0,
                min(
                    1.0,
                    dependency_score * 0.42
                    + context_score * 0.38
                    + stability_score * 0.14
                    + promotion_bonus
                    - promotion_penalty,
                ),
            ),
            4,
        )
        candidate_ready = bool(
            promotion_score >= 0.68
            and context_score >= 0.55
            and contradiction < 0.35
        )
        return {
            "system": self.system_name,
            "report_state": "final",
            "concept": str(concept or "runtime_concept"),
            "promotion_score": promotion_score,
            "promotion_dependency_score": round(dependency_score, 4),
            "promotion_context_score": round(context_score, 4),
            "promotion_bonus": promotion_bonus,
            "promotion_penalty": promotion_penalty,
            "candidate_ready": candidate_ready,
            "eligible_for_truth_candidate": candidate_ready,
            **context_telemetry,
            "promotion_reason": (
                "context_and_dependency_support_sufficient"
                if candidate_ready
                else "insufficient_context_support"
                if context_score < 0.55
                else "insufficient_promotion_score"
            ),
        }


def _average(values: Iterable[Any]) -> float:
    numbers = []
    for value in values:
        try:
            numbers.append(max(0.0, min(1.0, float(value))))
        except (TypeError, ValueError):
            continue
    return round(sum(numbers) / len(numbers), 4) if numbers else 0.0


def _score(mapping: Mapping[str, Any], *keys: str, default: float = 0.0) -> float:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            try:
                return round(max(0.0, min(1.0, float(value))), 4)
            except (TypeError, ValueError):
                return 0.0
    return round(max(0.0, min(1.0, float(default))), 4)


promotion_engine = PromotionEngine()


__all__ = ["PromotionEngine", "promotion_engine"]
