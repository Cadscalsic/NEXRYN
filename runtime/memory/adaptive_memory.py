# ============================================
# NEXRYN ADAPTIVE MEMORY
# ============================================

from runtime.memory.experience_manager import (
    ExperienceManager
)


# ============================================
# ADAPTIVE MEMORY
# ============================================

class AdaptiveMemory:

    def __init__(self):

        # ========================================
        # EXPERIENCE MANAGER
        # ========================================

        self.experience_manager = (
            ExperienceManager()
        )

    # ============================================
    # STORE EXPERIENCE
    # ============================================

    def learn(

        self,

        context
    ):

        self.experience_manager.store_experience(
            context
        )

    # ============================================
    # RETRIEVE EXPERIENCE GUIDANCE
    # ============================================

    def retrieve_guidance(

        self,

        patterns
    ):

        similar_experiences = (

            self.experience_manager.find_similar_experiences(
                patterns
            )
        )

        return similar_experiences

    # ============================================
    # ADAPT HYPOTHESES
    # ============================================

    def adapt_hypotheses(

        self,

        hypotheses,

        similar_experiences
    ):

        adapted = []

        similarity_boost = min(

            len(similar_experiences)
            * 0.02,

            0.10
        )

        for hypothesis in hypotheses:

            adapted_hypothesis = dict(
                hypothesis
            )

            old_confidence = (
                adapted_hypothesis.get(
                    "confidence",
                    0
                )
            )

            new_confidence = min(

                old_confidence
                + similarity_boost,

                1.0
            )

            adapted_hypothesis[
                "confidence"
            ] = round(
                new_confidence,
                4
            )

            adapted_hypothesis[
                "adaptive_boost"
            ] = round(
                similarity_boost,
                4
            )

            adapted.append(
                adapted_hypothesis
            )

        return adapted

    # ============================================
    # PRINT MEMORY STATUS
    # ============================================

    def print_status(self):

        self.experience_manager.print_report()