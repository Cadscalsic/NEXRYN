# ============================================
# NEXRYN COGNITIVE HOMEOSTASIS CONTROLLER
# ============================================


class HomeostasisController:

    def balance(self, metrics, dependency):

        stability_need = (
            metrics.get(
                "cognitive_fever_score",
                0.0,
            )
            +
            metrics.get(
                "identity_drift",
                0.0,
            )
        ) / 2

        exploration_need = max(
            0.0,
            1.0
            -
            stability_need
            -
            dependency.get(
                "dependency_risk",
                0.0,
            )
            * 0.25,
        )

        return {
            "system":
            "homeostasis_controller",

            "balances":
            {
                "exploration_vs_stability":
                {
                    "exploration":
                    round(
                        exploration_need,
                        4,
                    ),

                    "stability":
                    round(
                        stability_need,
                        4,
                    ),
                },

                "evolution_vs_continuity":
                "continuity_temporarily_prioritized"
                if stability_need >= 0.62
                else "balanced",

                "neurogenesis_vs_preservation":
                "defer_not_disable_neurogenesis",

                "abstraction_vs_grounding":
                "increase_grounding_when_entropy_rises",

                "adaptation_vs_constitutional_integrity":
                "constitution_sets_bounds",
            },

            "maximizes_stability":
            False,
        }
