# ============================================
# NEXRYN SEARCH REINFORCEMENT
# ============================================


# ============================================
# SEARCH REINFORCEMENT ENGINE
# ============================================

class SearchReinforcementEngine:

    def __init__(self):

        # ========================================
        # BOOST FACTOR
        # ========================================

        self.boost_factor = 0.1

    # ============================================
    # COMPUTE ADAPTIVE BOOST
    # ============================================

    def compute_boost(

        self,

        hypothesis,

        strategy_database
    ):

        strategy_name = hypothesis.get(
            "type",
            "unknown"
        )

        strategy_data = (

            strategy_database.get(
                strategy_name
            )
        )

        if strategy_data is None:

            return 0.0

        average_score = strategy_data.get(
            "average_score",
            0.0
        )

        adaptive_boost = (

            average_score

            *

            self.boost_factor
        )

        return round(
            adaptive_boost,
            4
        )

    # ============================================
    # APPLY BOOSTS
    # ============================================

    def apply_boosts(

        self,

        hypotheses,

        strategy_database
    ):

        boosted_hypotheses = []

        for hypothesis in hypotheses:

            adaptive_boost = (

                self.compute_boost(

                    hypothesis,

                    strategy_database
                )
            )

            boosted_hypothesis = dict(
                hypothesis
            )

            original_confidence = (

                hypothesis.get(
                    "confidence",
                    0.0
                )
            )

            boosted_confidence = (

                original_confidence

                +

                adaptive_boost
            )

            boosted_confidence = min(
                boosted_confidence,
                1.0
            )

            boosted_hypothesis[
                "adaptive_boost"
            ] = adaptive_boost

            boosted_hypothesis[
                "confidence"
            ] = round(
                boosted_confidence,
                4
            )

            boosted_hypotheses.append(
                boosted_hypothesis
            )

        return boosted_hypotheses