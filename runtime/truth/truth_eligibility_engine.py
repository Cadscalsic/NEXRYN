"""Truth candidate eligibility evaluation."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.context.context_validator import validate_context_collection


class TruthEligibilityEngine:
    """Evaluate whether promoted concepts can become truth candidates."""

    system_name = "truth_eligibility_engine"

    def evaluate_eligibility(
        self,
        concept: str,
        promotion_report: Mapping[str, Any] | None = None,
        contexts: Iterable[Mapping[str, Any]] | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        promotion_report = (
            promotion_report
            if isinstance(promotion_report, Mapping)
            else {}
        )
        runtime_context = runtime_context if isinstance(runtime_context, Mapping) else {}
        contexts, context_telemetry = validate_context_collection(contexts)

        dependency_coherence = _score(
            promotion_report,
            "promotion_dependency_score",
            default=_score(
                runtime_context,
                "dependency_coherence_average",
                "dependency_chain_coverage",
                default=0.0,
            ),
        )
        dependency_coverage = _score(
            runtime_context,
            "dependency_chain_coverage",
            default=dependency_coherence,
        )
        context_support = _context_support(contexts)
        causal_alignment = _average(context.get("causal_score", 0.0) for context in contexts)
        identity_continuity = _average(
            context.get("identity_score", 0.72)
            for context in contexts
        ) if contexts else 0.72
        contradiction_score = _score(
            runtime_context,
            "contradiction_score",
            default=0.0,
        )
        stability_score = _average(
            context.get("stability_score", 0.0)
            for context in contexts
        )
        support_saturation = min(1.0, (dependency_coverage + context_support) / 2)

        eligibility_score = round(
            dependency_coherence * 0.22
            + dependency_coverage * 0.16
            + context_support * 0.24
            + causal_alignment * 0.12
            + identity_continuity * 0.10
            + stability_score * 0.10
            + support_saturation * 0.06
            - contradiction_score * 0.25,
            4,
        )
        eligibility_score = max(0.0, min(1.0, eligibility_score))
        blocking_factors = []
        if context_support < 0.55:
            blocking_factors.append("insufficient_context_support")
        if dependency_coherence < 0.50:
            blocking_factors.append("insufficient_dependency_coherence")
        if contradiction_score >= 0.35:
            blocking_factors.append("contradiction_above_threshold")
        eligible = eligibility_score >= 0.68 and not blocking_factors
        return {
            "system": self.system_name,
            "report_state": "final",
            "concept": str(concept or "runtime_concept"),
            "eligible_for_truth_candidate": bool(eligible),
            "eligibility_score": eligibility_score,
            "dependency_coherence": dependency_coherence,
            "dependency_coverage": dependency_coverage,
            "context_support": context_support,
            "causal_alignment": causal_alignment,
            "identity_continuity": identity_continuity,
            "contradiction_score": contradiction_score,
            "stability_score": stability_score,
            "support_saturation": round(support_saturation, 4),
            "blocking_factors": blocking_factors,
            **context_telemetry,
            "recommended_next_step": (
                "generate_truth_candidate"
                if eligible
                else blocking_factors[0]
                if blocking_factors
                else "collect_more_evidence"
            ),
        }


def _context_support(contexts: list[Mapping[str, Any]]) -> float:
    return _average(context.get("confidence", 0.0) for context in contexts)


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


truth_eligibility_engine = TruthEligibilityEngine()


__all__ = ["TruthEligibilityEngine", "truth_eligibility_engine"]
