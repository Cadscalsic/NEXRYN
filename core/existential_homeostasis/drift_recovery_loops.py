def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class DriftRecoveryLoops:

    def recover(self, context):

        drift_cost = _clamp(
            context.get("existential_economics_report", {})
            .get("drift_cost", {})
            .get("drift_cost", 0.0)
        )

        loops = []

        if drift_cost >= 0.32:

            loops = [
                "semantic_drift_reversal",
                "identity_anchor_revalidation",
                "causal_continuity_recheck",
            ]

        return {
            "system": "drift_recovery_loops",
            "drift_cost": drift_cost,
            "recovery_loops": loops,
            "recovery_state": (
                "drift_recovery_active"
                if loops
                else "drift_recovery_standby"
            ),
        }
