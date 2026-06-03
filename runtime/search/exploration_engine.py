# ============================================
# NEXRYN EXPLORATION ENGINE
# ============================================

import random


# ============================================
# EXPLORATION ENGINE
# ============================================

class ExplorationEngine:

    def __init__(self):

        # ========================================
        # EXPLORATION RATE
        # ========================================

        self.exploration_rate = 0.20

    # ============================================
    # SHOULD EXPLORE
    # ============================================

    def should_explore(self):

        random_value = random.random()

        return (
            random_value < self.exploration_rate
        )

    # ============================================
    # APPLY EXPLORATION
    # ============================================

    def apply_exploration(

        self,

        hypotheses
    ):

        if not hypotheses:

            return hypotheses

        # ========================================
        # EXPLOITATION MODE
        # ========================================

        if not self.should_explore():

            return hypotheses

        # ========================================
        # EXPLORATION MODE
        # ========================================

        explored = []

        for hypothesis in hypotheses:

            modified = dict(
                hypothesis
            )

            original_confidence = (

                modified.get(
                    "confidence",
                    0.0
                )
            )

            exploration_bonus = 0.05

            modified[
                "confidence"
            ] = round(

                min(
                    original_confidence
                    +
                    exploration_bonus,

                    1.0
                ),

                4
            )

            modified[
                "exploration_applied"
            ] = True

            explored.append(
                modified
            )

        return explored