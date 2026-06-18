"""Graded process-context strength estimation."""

from __future__ import annotations

from typing import Any, Mapping

from core.epistemic_models import clamp


class ProcessStrengthEstimator:
    """Estimate process strength with penalties instead of hard zeroing."""

    system_name = "process_strength_estimator"

    def estimate(
        self,
        extracted_context: Mapping[str, Any],
        dependency_confidence: float = 0.0,
        causal_alignment: float = 0.0,
        identity_continuity: float = 0.0,
    ) -> dict[str, Any]:
        penalties = []
        evidence_score = 0.0
        for key in (
            "preconditions",
            "transition_signature",
            "postconditions",
            "invariants",
            "dependency_links",
        ):
            if extracted_context.get(key) or (
                key == "transition_signature"
                and extracted_context.get("transitions")
            ):
                evidence_score += 0.12
            else:
                penalties.append(f"{key}_missing")
        if extracted_context.get("temporal_signature", {}).get(
            "state_sequence_represented"
        ):
            evidence_score += 0.10
        else:
            penalties.append("state_transition_state_signature_missing")

        strength = clamp(
            dependency_confidence * 0.24
            + causal_alignment * 0.24
            + identity_continuity * 0.22
            + evidence_score
        )
        penalty_weight = min(len(penalties) * 0.035, 0.21)
        final_strength = clamp(min(strength - penalty_weight, 0.97))
        return {
            "system": self.system_name,
            "process_context_strength": round(final_strength, 4),
            "graded_penalties": penalties,
            "missing_process_evidence_penalty": round(penalty_weight, 4),
            "process_context_ready": final_strength >= 0.85,
        }


__all__ = ["ProcessStrengthEstimator"]
