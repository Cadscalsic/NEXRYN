def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class HybridIdentityBalancer:

    BALANCE_THRESHOLD = 0.56
    CRITICAL_THRESHOLD = 0.40
    HIGH_FUSION_PRESSURE = 0.72

    def balance(self, context=None, conflict=None):
        context = context or {}
        conflict = conflict or {}

        identity_resilience = _clamp(
            context.get("adaptive_equilibrium_report", {})
            .get("resilient_identity_core", {})
            .get("identity_resilience", 0.5)
        )

        conflict_score = _clamp(
            conflict.get("paradigm_conflict_score", 0.0)
        )

        fusion_pressure = _clamp(
            context.get("existential_pressure_report", {})
            .get("merge_pressure_balancer", {})
            .get("merge_pressure", 0.0)
        )

        hybrid_balance = _clamp(
            identity_resilience * 0.58
            + (1.0 - conflict_score) * 0.24
            + (1.0 - fusion_pressure) * 0.18
        )

        fast_mode = (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
        )

        critical = (
            hybrid_balance < self.CRITICAL_THRESHOLD
            or fusion_pressure >= self.HIGH_FUSION_PRESSURE
        )

        needs_balance = hybrid_balance < self.BALANCE_THRESHOLD

        if fast_mode and needs_balance and not critical:
            return {
                "system": "hybrid_identity_balancer",
                "identity_resilience": identity_resilience,
                "fusion_pressure": fusion_pressure,
                "hybrid_identity_balance": hybrid_balance,
                "identity_balance_state": "identity_balance_deferred_in_fast_mode",
                "identity_actions": [],
                "deferred_actions": [
                    "separate_paradigm_identity_layers",
                    "keep_hybrid_identity_probationary",
                ],
                "critical": False,
                "needs_balance": True,
                "reason": "noncritical_identity_balancing_deferred_after_success",
                "scores": {
                    "identity_resilience": identity_resilience,
                    "paradigm_conflict_score": conflict_score,
                    "fusion_pressure": fusion_pressure,
                },
            }

        if critical:
            actions = [
                "separate_paradigm_identity_layers",
                "keep_hybrid_identity_probationary",
                "block_identity_merge_commit",
            ]
            state = "hybrid_identity_balance_critical"

        elif needs_balance:
            actions = [
                "separate_paradigm_identity_layers",
                "keep_hybrid_identity_probationary",
            ]
            state = "hybrid_identity_balancing_active"

        else:
            actions = []
            state = "hybrid_identity_balanced"

        return {
            "system": "hybrid_identity_balancer",
            "identity_resilience": identity_resilience,
            "fusion_pressure": fusion_pressure,
            "hybrid_identity_balance": hybrid_balance,
            "identity_balance_state": state,
            "identity_actions": actions,
            "critical": critical,
            "needs_balance": needs_balance,
            "scores": {
                "identity_resilience": identity_resilience,
                "paradigm_conflict_score": conflict_score,
                "fusion_pressure": fusion_pressure,
            },
        }