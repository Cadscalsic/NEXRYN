def _clamp(value, minimum=0.0, maximum=1.0):
    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticCoexistenceEngine:

    COEXISTENCE_THRESHOLD = 0.58
    CRITICAL_THRESHOLD = 0.42
    MAX_ROUTE_BONUS = 0.24

    def compute(self, identity=None, router=None, absorption=None, runtime_context=None):
        identity = identity or {}
        router = router or {}
        absorption = absorption or {}
        runtime_context = runtime_context or {}

        identity_balance = _clamp(identity.get("hybrid_identity_balance", 0.0))

        route_count = len(router.get("semantic_routes", []))
        route_support = _clamp(min(route_count * 0.08, self.MAX_ROUTE_BONUS))

        absorption_score = _clamp(
            absorption.get("hybrid_drift_absorption", 0.0)
        )

        coexistence = _clamp(
            identity_balance * 0.50
            + route_support * 0.14
            + absorption_score * 0.36
        )

        fast_mode = (
            runtime_context.get("episode_completed") is True
            or runtime_context.get("shutdown_mode") == "fast"
            or runtime_context.get("post_success_mode") == "fast"
        )

        critical = coexistence < self.CRITICAL_THRESHOLD
        guarded = coexistence < self.COEXISTENCE_THRESHOLD

        if fast_mode and guarded and not critical:
            return {
                "system": "semantic_coexistence_engine",
                "semantic_coexistence": coexistence,
                "coexistence_state": "coexistence_deferred_in_fast_mode",
                "coexistence_actions": [],
                "deferred_actions": [
                    "maintain_parallel_paradigm_representations",
                    "avoid_forced_semantic_unification",
                ],
                "critical": False,
                "reason": "noncritical_semantic_coexistence_deferred_after_success",
                "scores": {
                    "identity_balance": identity_balance,
                    "route_count": route_count,
                    "route_support": route_support,
                    "absorption_score": absorption_score,
                },
            }

        if critical:
            actions = [
                "maintain_parallel_paradigm_representations",
                "avoid_forced_semantic_unification",
                "block_semantic_unification_commit",
            ]
            state = "semantic_coexistence_critical"

        elif guarded:
            actions = [
                "maintain_parallel_paradigm_representations",
                "avoid_forced_semantic_unification",
            ]
            state = "semantic_coexistence_guarded"

        else:
            actions = ["allow_attested_semantic_coexistence"]
            state = "semantic_coexistence_viable"

        return {
            "system": "semantic_coexistence_engine",
            "semantic_coexistence": coexistence,
            "coexistence_actions": actions,
            "coexistence_state": state,
            "critical": critical,
            "guarded": guarded,
            "scores": {
                "identity_balance": identity_balance,
                "route_count": route_count,
                "route_support": route_support,
                "absorption_score": absorption_score,
            },
        }