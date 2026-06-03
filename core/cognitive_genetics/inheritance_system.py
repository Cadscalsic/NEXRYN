# ============================================
# NEXRYN GENETIC INHERITANCE SYSTEM
# ============================================

from core.cognitive_genetics.genetic_traits import (
    clamp,
)


class InheritanceSystem:

    def inherit(self, traits, reputation_report):

        reputations = {
            item["trait_name"]: item
            for item in reputation_report.get(
                "trait_reputations",
                [],
            )
        }

        inherited = []

        for trait in traits:

            reputation = reputations.get(
                trait["trait_name"],
                {},
            )

            strength = clamp(
                trait.get(
                    "inheritance_strength",
                    0.0,
                )
                * 0.70
                +
                reputation.get(
                    "epistemic_legitimacy_score",
                    0.0,
                )
                * 0.30
            )

            inherited.append({
                "trait_name": trait["trait_name"],
                "inheritance_strength": strength,
                "lineage_transmission": (
                    "preserve_core_trait"
                    if trait.get(
                        "constitutional_priority",
                        0.0,
                    )
                    >= 0.82
                    else "adaptive_trait"
                ),
                "long_term_trait_drift_monitoring": True,
            })

        return {
            "system": "inheritance_system",
            "inherited_traits": inherited,
            "constitutional_preservation": True,
            "safe_adaptive_evolution": True,
        }
