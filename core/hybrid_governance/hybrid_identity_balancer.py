def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class HybridIdentityBalancer:

    def balance(self, context, conflict):

        identity_resilience = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("resilient_identity_core", {})
            .get("identity_resilience", 0.5)
        )
        conflict_score = _clamp(conflict.get("paradigm_conflict_score", 0.0))
        fusion_pressure = _clamp(
            context.get("existential_pressure_report", {})
            .get("merge_pressure_balancer", {})
            .get("merge_pressure", 0.0)
        )

        hybrid_balance = _clamp(
            identity_resilience * 0.58
            +
            (1.0 - conflict_score) * 0.24
            +
            (1.0 - fusion_pressure) * 0.18
        )

        return {
            "system": "hybrid_identity_balancer",
            "identity_resilience": identity_resilience,
            "fusion_pressure": fusion_pressure,
            "hybrid_identity_balance": hybrid_balance,
            "identity_actions": [
                "separate_paradigm_identity_layers",
                "keep_hybrid_identity_probationary",
            ]
            if hybrid_balance < 0.56
            else [],
            "identity_balance_state": (
                "hybrid_identity_balancing_active"
                if hybrid_balance < 0.56
                else "hybrid_identity_balanced"
            ),
        }
