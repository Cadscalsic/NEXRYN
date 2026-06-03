def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class DriftAbsorptionEngine:

    def absorb(self, context, fatigue):

        drift_cost = _clamp(
            context.get("existential_economics_report", {})
            .get("drift_cost", {})
            .get("drift_cost", 0.0)
        )
        absorption_need = _clamp(
            drift_cost * 0.58
            +
            fatigue.get("semantic_fatigue", 0.0) * 0.42
        )

        return {
            "system": "drift_absorption_engine",
            "drift_cost": drift_cost,
            "absorption_need": absorption_need,
            "absorption_actions": [
                "absorb_drift_into_stabilizing_buffers",
                "route_drift_through_recovery_loops",
            ]
            if absorption_need >= 0.34
            else [],
            "absorption_state": (
                "drift_absorption_active"
                if absorption_need >= 0.34
                else "drift_absorption_standby"
            ),
        }
