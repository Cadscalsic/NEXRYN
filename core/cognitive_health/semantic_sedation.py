# ============================================
# NEXRYN SEMANTIC SEDATION
# ============================================


class SemanticSedation:

    def recommend(self, dosage):

        intensity = dosage.get(
            "semantic_sedation",
            0.0,
        )

        return {
            "treatment":
            "SEMANTIC_SEDATION",

            "intent":
            "temporarily_reduce_semantic_expansion_without_permanent_suppression",

            "intensity":
            intensity,

            "effects":
            {
                "fusion_intensity":
                "reduce_temporarily",

                "recursion_depth":
                "throttle_temporarily",

                "semantic_expansion":
                "slow",

                "neurogenesis_rate":
                "defer_not_disable",
            },

            "permanent_sedation":
            False,
        }
