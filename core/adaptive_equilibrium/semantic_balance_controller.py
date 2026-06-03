def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticBalanceController:

    def balance(self, context, drift_report):

        semantic = context.get("existential_homeostasis_report", {}).get(
            "semantic_equilibrium",
            {},
        )
        fatigue = context.get("existential_pressure_report", {}).get(
            "semantic_fatigue_cycles",
            {},
        )

        equilibrium = _clamp(semantic.get("semantic_equilibrium", 0.5))
        semantic_fatigue = _clamp(fatigue.get("semantic_fatigue", 0.0))
        assimilated_drift = _clamp(drift_report.get("assimilated_drift", 0.0))

        semantic_balance = _clamp(
            equilibrium * 0.56
            +
            (1.0 - semantic_fatigue) * 0.26
            +
            assimilated_drift * 0.18
        )

        return {
            "system": "semantic_balance_controller",
            "semantic_balance": semantic_balance,
            "semantic_actions": [
                "rebalance_semantic_load",
                "protect_core_anchors_during_assimilation",
            ]
            if semantic_balance < 0.56
            else [],
            "semantic_balance_state": (
                "semantic_balance_recovering"
                if semantic_balance < 0.56
                else "semantic_balance_stable"
            ),
        }
