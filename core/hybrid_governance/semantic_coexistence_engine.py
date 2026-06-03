def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticCoexistenceEngine:

    def compute(self, identity, router, absorption):

        identity_balance = _clamp(identity.get("hybrid_identity_balance", 0.0))
        route_support = _clamp(len(router.get("semantic_routes", [])) * 0.12)
        absorption_score = _clamp(absorption.get("hybrid_drift_absorption", 0.0))

        coexistence = _clamp(
            identity_balance * 0.46
            +
            route_support * 0.20
            +
            absorption_score * 0.34
        )

        return {
            "system": "semantic_coexistence_engine",
            "semantic_coexistence": coexistence,
            "coexistence_actions": [
                "maintain_parallel_paradigm_representations",
                "avoid_forced_semantic_unification",
            ]
            if coexistence < 0.58
            else [
                "allow_attested_semantic_coexistence",
            ],
            "coexistence_state": (
                "semantic_coexistence_guarded"
                if coexistence < 0.58
                else "semantic_coexistence_viable"
            ),
        }
