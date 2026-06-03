def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class PropagationStabilityManager:

    def manage(self, context):

        failure_propagation = _clamp(
            context.get("concept_lifecycle_report", {}).get(
                "failure_propagation_score",
                context.get("failure_propagation_score", 0.0),
            )
        )
        resonance = _clamp(
            context.get("existential_pressure_report", {})
            .get("resonance_stability_control", {})
            .get("resonance_risk", 0.0)
        )

        stability = _clamp(1.0 - (failure_propagation * 0.58 + resonance * 0.42))

        return {
            "system": "propagation_stability_manager",
            "failure_propagation_score": failure_propagation,
            "resonance_risk": resonance,
            "propagation_stability": stability,
            "propagation_actions": [
                "contain_failure_propagation",
                "localize_unstable_updates",
            ]
            if stability < 0.58
            else [],
            "propagation_state": (
                "propagation_stability_managed"
                if stability < 0.58
                else "propagation_stability_clear"
            ),
        }
