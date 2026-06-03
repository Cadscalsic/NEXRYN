def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class DriftAssimilation:

    def assimilate(self, context):

        drift = _clamp(
            context.get("existential_economics_report", {})
            .get("drift_cost", {})
            .get("drift_cost", 0.0)
        )
        absorption = _clamp(
            context.get("existential_pressure_report", {})
            .get("drift_absorption", {})
            .get("absorption_need", 0.0)
        )

        assimilation_capacity = _clamp(1.0 - absorption * 0.48)
        assimilated_drift = _clamp(min(drift, assimilation_capacity) * 0.72)

        return {
            "system": "drift_assimilation",
            "drift_cost": drift,
            "assimilation_capacity": assimilation_capacity,
            "assimilated_drift": assimilated_drift,
            "assimilation_actions": [
                "convert_low_risk_drift_to_adaptive_variation",
                "route_high_risk_drift_to_recovery",
            ]
            if drift >= 0.24
            else [],
            "assimilation_state": (
                "drift_assimilation_active"
                if drift >= 0.24
                else "drift_assimilation_idle"
            ),
        }
