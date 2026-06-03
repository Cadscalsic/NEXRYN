# ============================================
# NEXRYN SEMANTIC TEMPERAMENT
# ============================================


class SemanticTemperament:

    def select(self, context):

        entropy = context.get(
            "runtime_entropy",
            0.0,
        )

        drift = context.get(
            "identity_drift",
            0.0,
        )

        if entropy >= 0.70:
            temperament = "stabilizing"
        elif drift >= 0.45:
            temperament = "reflective"
        elif context.get(
            "exploration_suppression_rate",
            0.0,
        ) >= 0.55:
            temperament = "exploratory"
        else:
            temperament = "adaptive"

        return {
            "system": "semantic_temperament",
            "temperament": temperament,
            "available_temperaments": [
                "exploratory",
                "analytical",
                "stabilizing",
                "cooperative",
                "reflective",
                "cautious",
                "adaptive",
                "reconstructive",
            ],
            "not_personality": True,
            "rigid_identity": False,
        }
