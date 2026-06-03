def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ExistentialDriftBalancer:

    def balance(self, context):

        drift = _clamp(
            context.get("existential_economics_report", {})
            .get("drift_cost", {})
            .get("drift_cost", 0.0)
        )
        assimilation = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("drift_assimilation", {})
            .get("assimilated_drift", 0.0)
        )

        containment_need = _clamp(drift * 0.70 - assimilation * 0.30)

        return {
            "system": "existential_drift_balancer",
            "drift_cost": drift,
            "assimilated_drift": assimilation,
            "containment_need": containment_need,
            "drift_actions": [
                "contain_existential_drift",
                "separate_adaptive_drift_from_identity_drift",
            ]
            if containment_need >= 0.30
            else [],
            "drift_state": (
                "existential_drift_containment_active"
                if containment_need >= 0.30
                else "existential_drift_balanced"
            ),
        }
