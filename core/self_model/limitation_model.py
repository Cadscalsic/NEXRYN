# ============================================
# NEXRYN LIMITATION MODEL
# ============================================


class LimitationModel:

    def detect_limitations(self, context):

        limitations = []

        entropy = context.get(
            "runtime_entropy",
            context.get(
                "cognitive_entropy_report",
                {},
            ).get(
                "runtime_entropy",
                0.0,
            ),
        )

        if entropy >= 0.70:

            limitations.append({
                "limitation":
                "semantic_overheating",

                "severity":
                "critical",

                "cause":
                "high_runtime_entropy",
            })

        recursion = context.get(
            "recursive_pressure_governor_report",
            {},
        )

        if recursion.get(
            "pressure_state",
        ) == "capped":

            limitations.append({
                "limitation":
                "unsafe_recursion_depth",

                "severity":
                "high",

                "cause":
                "recursive_pressure_governor",
            })

        promotion = context.get(
            "novelty_promotion_gate_report",
            {},
        )

        if promotion.get(
            "decision_counts",
            {},
        ).get(
            "promote",
            0,
        ) == 0 and promotion:

            limitations.append({
                "limitation":
                "immature_novel_concepts",

                "severity":
                "moderate",

                "cause":
                "novelty_promotion_gate",
            })

        return {
            "limitations":
            limitations,

            "limitation_count":
            len(
                limitations,
            ),
        }
