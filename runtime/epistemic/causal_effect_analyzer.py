from core.epistemic_models import clamp


class CausalEffectAnalyzer:
    def analyze(self, completed_experiments):
        measurements = []
        for result in completed_experiments or []:
            baseline = clamp(result["baseline_execution_result"])
            intervention = clamp(result["intervention_execution_result"])
            baseline_contradiction = clamp(
                result.get("baseline_contradiction_score", 0.0)
            )
            intervention_contradiction = clamp(
                result.get("intervention_contradiction_score", 0.0)
            )
            causal_effect_delta = clamp(abs(baseline - intervention))
            contradiction_delta = round(
                intervention_contradiction - baseline_contradiction,
                4,
            )
            measurements.append({
                **result,
                "causal_effect_delta": causal_effect_delta,
                "contradiction_delta": contradiction_delta,
                "measured_causal_alignment": causal_effect_delta,
                "measured_contradiction_score": intervention_contradiction,
                "measured_support_score": baseline,
                "analysis_state": (
                    "DIRECT_CAUSAL_EFFECT_OBSERVED"
                    if causal_effect_delta >= 0.20
                    else "WEAK_CAUSAL_EFFECT_OBSERVED"
                ),
            })

        return {
            "system": "causal_effect_analyzer",
            "phase": "5.6",
            "measurements": measurements,
            "direct_causal_effect_count": sum(
                item["analysis_state"]
                == "DIRECT_CAUSAL_EFFECT_OBSERVED"
                for item in measurements
            ),
            "causal_effect_is_measured_not_assumed": True,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "CausalEffectAnalyzer",
]
