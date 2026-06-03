# ============================================
# NEXRYN TRAIT STABILITY MONITOR
# ============================================

from core.cognitive_genetics.genetic_traits import (
    clamp,
)


class TraitStabilityMonitor:

    def monitor(self, traits):

        weak = [
            trait["trait_name"]
            for trait in traits
            if trait.get(
                "stability_score",
                0.0,
            )
            < 0.52
        ]

        average = clamp(
            sum(
                trait.get(
                    "stability_score",
                    0.0,
                )
                for trait in traits
            )
            /
            max(len(traits), 1)
        )

        return {
            "system": "trait_stability_monitor",
            "average_stability": average,
            "weak_traits": weak,
            "stability_state": (
                "stable_genome"
                if average >= 0.68 and not weak
                else "trait_rehabilitation_required"
            ),
        }
