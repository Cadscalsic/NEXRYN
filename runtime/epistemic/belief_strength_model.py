from core.epistemic_models import clamp


class BeliefStrengthModel:
    def evaluate(self, aggregate, trial_result):
        strength = clamp(
            aggregate.evidence_strength * 0.38
            + (1.0 - aggregate.contradiction_score) * 0.22
            + aggregate.semantic_consistency * 0.18
            + aggregate.causal_alignment * 0.14
            + min(aggregate.evidence_count, 4) / 4 * 0.08
        )
        state = (
            "REJECTED"
            if trial_result == "FAILED"
            else "SUPPORTED"
            if trial_result == "PASSED"
            and strength >= 0.68
            else "PROBATION"
            if strength >= 0.48
            else "CANDIDATE"
        )
        return {
            "belief_strength": strength,
            "recommended_state": state,
            "confidence_is_not_truth": True,
            "causal_validation_required_for_truth": True,
        }


__all__ = [
    "BeliefStrengthModel",
]
