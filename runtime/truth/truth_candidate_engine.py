"""Generate truth candidates from promotion and eligibility reports."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from runtime.context.context_validator import validate_context_collection


class TruthCandidateEngine:
    """Create explicit truth candidates only when gates are satisfied."""

    system_name = "truth_candidate_engine"

    def generate(
        self,
        concept: str,
        promotion_report: Mapping[str, Any] | None = None,
        eligibility_report: Mapping[str, Any] | None = None,
        contexts: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any]:
        promotion_report = (
            promotion_report
            if isinstance(promotion_report, Mapping)
            else {}
        )
        eligibility_report = (
            eligibility_report
            if isinstance(eligibility_report, Mapping)
            else {}
        )
        contexts, context_telemetry = validate_context_collection(contexts)
        ready = promotion_report.get("candidate_ready") is True
        eligible = eligibility_report.get("eligible_for_truth_candidate") is True
        if not ready or not eligible:
            reason = (
                "promotion_not_ready"
                if not ready
                else "eligibility_blocked"
            )
            return {
                "system": self.system_name,
                "report_state": "final",
                "result_count": 0,
                "truth_candidates": [],
                "candidate_generated": False,
                "candidate_rejected": True,
                "reason": reason,
                **context_telemetry,
                "blocking_factors": eligibility_report.get("blocking_factors", []),
            }

        candidate = {
            "concept": str(concept or "runtime_concept"),
            "candidate_confidence": _mean(
                promotion_report.get("promotion_score", 0.0),
                eligibility_report.get("eligibility_score", 0.0),
            ),
            "dependency_support": promotion_report.get(
                "promotion_dependency_score",
                0.0,
            ),
            "context_support": promotion_report.get("promotion_context_score", 0.0),
            "causal_support": _average(
                context.get("causal_score", 0.0)
                for context in contexts
            ),
            "identity_support": _average(
                context.get("identity_score", 0.0)
                for context in contexts
            ),
            "contradiction_score": eligibility_report.get(
                "contradiction_score",
                0.0,
            ),
            "promotion_score": promotion_report.get("promotion_score", 0.0),
            "candidate_state": "TRUTH_CANDIDATE",
        }
        return {
            "system": self.system_name,
            "report_state": "final",
            "result_count": 1,
            "truth_candidates": [candidate],
            "candidate_generated": True,
            "candidate_rejected": False,
            "reason": "candidate_ready_and_eligible",
            **context_telemetry,
        }


def _mean(*values: Any) -> float:
    return _average(values)


def _average(values: Iterable[Any]) -> float:
    numbers = []
    for value in values:
        try:
            numbers.append(max(0.0, min(1.0, float(value))))
        except (TypeError, ValueError):
            continue
    return round(sum(numbers) / len(numbers), 4) if numbers else 0.0


truth_candidate_engine = TruthCandidateEngine()


__all__ = ["TruthCandidateEngine", "truth_candidate_engine"]
