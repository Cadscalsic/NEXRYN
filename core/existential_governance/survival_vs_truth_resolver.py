def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SurvivalVsTruthResolver:

    def resolve(self, context, epistemic):

        survival_pressure = _clamp(
            context.get("existential_pressure_report", {}).get(
                "managed_pressure",
                0.0,
            )
        )
        truth_confidence = _clamp(epistemic.get("epistemic_confidence", 0.5))
        continuity = _clamp(
            context.get("existential_homeostasis_report", {})
            .get("continuity_equilibrium", {})
            .get("continuity_equilibrium", 0.5)
        )

        truth_priority = _clamp(
            truth_confidence * 0.52
            +
            continuity * 0.28
            +
            (1.0 - survival_pressure) * 0.20
        )

        return {
            "system": "survival_vs_truth_resolver",
            "survival_pressure": survival_pressure,
            "truth_priority": truth_priority,
            "resolution_policy": (
                "truth_preservation_over_short_term_survival"
                if truth_priority >= 0.58
                else "survival_action_requires_truth_attestation"
            ),
            "resolver_actions": [
                "block_survival_override_of_absolute_invariants",
                "require_truth_attestation_for_emergency_adaptation",
            ]
            if truth_priority < 0.58 or survival_pressure >= 0.62
            else [],
        }
