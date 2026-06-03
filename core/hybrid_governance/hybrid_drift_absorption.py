def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class HybridDriftAbsorption:

    def absorb(self, context, conflict):

        assimilated = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("drift_assimilation", {})
            .get("assimilated_drift", 0.0)
        )
        conflict_score = _clamp(conflict.get("paradigm_conflict_score", 0.0))

        hybrid_absorption = _clamp(assimilated * 0.60 + (1.0 - conflict_score) * 0.24)

        return {
            "system": "hybrid_drift_absorption",
            "hybrid_drift_absorption": hybrid_absorption,
            "absorption_actions": [
                "absorb_cross_paradigm_drift_in_buffers",
            ]
            if hybrid_absorption >= 0.28
            else [],
            "absorption_state": (
                "hybrid_drift_absorption_active"
                if hybrid_absorption >= 0.28
                else "hybrid_drift_absorption_standby"
            ),
        }
