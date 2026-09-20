"""Adaptive validation thresholds for stable and unstable concepts."""

from __future__ import annotations

from typing import Any, Mapping


class AdaptiveValidationThresholds:
    def evaluate(
        self,
        metrics: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        data = dict(metrics or {})
        concept_stability = self._number(data.get("concept_stability", 0.5))
        contradiction_score = self._number(data.get("contradiction_score", 0.0))
        support_threshold = self._number(data.get("base_support_threshold", 0.85))
        required_evidence = int(self._number(data.get("base_required_evidence", 10)))

        if concept_stability > 0.95:
            support_threshold = max(0.70, support_threshold - 0.10)
            required_evidence = max(3, required_evidence - 5)
        if contradiction_score > 0.30:
            support_threshold = min(0.95, support_threshold + 0.10)
            required_evidence = min(20, required_evidence + 5)
        return {
            "support_threshold": support_threshold,
            "required_evidence": required_evidence,
            "contradiction_limit": 0.30 if contradiction_score <= 0.30 else 0.10,
            "stable_concept_discount_applied": concept_stability > 0.95,
            "unstable_concept_review_applied": contradiction_score > 0.30,
        }

    def _number(self, value: Any) -> float:
        try:
            return max(0.0, float(value))
        except (TypeError, ValueError):
            return 0.0


adaptive_validation_thresholds = AdaptiveValidationThresholds()


__all__ = [
    "AdaptiveValidationThresholds",
    "adaptive_validation_thresholds",
]
