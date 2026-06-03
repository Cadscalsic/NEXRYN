def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ContinuityEthicsEngine:

    def judge(self, context, survival_truth):

        continuity = _clamp(
            context.get("existential_homeostasis_report", {})
            .get("continuity_equilibrium", {})
            .get("continuity_equilibrium", 0.5)
        )
        identity = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("resilient_identity_core", {})
            .get("identity_resilience", 0.5)
        )
        truth_priority = _clamp(survival_truth.get("truth_priority", 0.5))

        ethics_score = _clamp(
            continuity * 0.38
            +
            identity * 0.30
            +
            truth_priority * 0.32
        )

        return {
            "system": "continuity_ethics_engine",
            "continuity_ethics_score": ethics_score,
            "ethics_actions": [
                "preserve_cognitive_continuity_over_opportunistic_adaptation",
                "require_ethics_review_for_identity_altering_change",
            ]
            if ethics_score < 0.58
            else [],
            "ethics_state": (
                "continuity_ethics_review_active"
                if ethics_score < 0.58
                else "continuity_ethics_clear"
            ),
        }
