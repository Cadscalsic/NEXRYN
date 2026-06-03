# ============================================
# NEXRYN TRAIT REPUTATION SYSTEM
# ============================================

from core.cognitive_genetics.genetic_traits import (
    clamp,
)


class TraitReputationSystem:

    def evaluate(self, traits, context):

        epistemic = context.get(
            "epistemic_constitution_report",
            {},
        ).get(
            "epistemic_legitimacy_engine",
            {},
        )

        truth_score = epistemic.get(
            "truth_score",
            0.5,
        )

        dependency = context.get(
            "cognitive_pharmacy_report",
            {},
        ).get(
            "dependency_prevention",
            {},
        ).get(
            "dependency_risk",
            0.0,
        )

        reports = []

        for trait in traits:

            stability = trait.get(
                "stability_score",
                0.0,
            )

            legitimacy = clamp(
                truth_score * 0.40
                +
                stability * 0.35
                +
                trait.get(
                    "historical_stability",
                    0.0,
                )
                * 0.25
                -
                dependency * 0.10
            )

            report = {
                "trait_name": trait.get(
                    "trait_name",
                ),
                "long_term_stability_history": trait.get(
                    "historical_stability",
                    0.0,
                ),
                "epistemic_legitimacy_score": legitimacy,
                "adaptation_quality": trait.get(
                    "evolutionary_flexibility",
                    0.0,
                ),
                "historical_survival_record": trait.get(
                    "inheritance_strength",
                    0.0,
                ),
                "constitutional_reliability": clamp(
                    trait.get(
                        "constitutional_priority",
                        0.0,
                    )
                    *
                    trait.get(
                        "mutation_resistance",
                        0.0,
                    )
                ),
                "reputation_state": (
                    "established"
                    if legitimacy >= 0.68
                    else "rehabilitation_observation"
                    if legitimacy < 0.36
                    else "forming"
                ),
            }

            reports.append(report)

        average = clamp(
            sum(
                item["epistemic_legitimacy_score"]
                for item in reports
            )
            /
            max(
                len(
                    reports,
                ),
                1,
            )
        )

        return {
            "system": "trait_reputation_system",
            "trait_reputations": reports,
            "average_trait_reputation": average,
            "reputation_state": (
                "genome_reliable"
                if average >= 0.68
                else "genome_forming"
                if average >= 0.42
                else "genome_rehabilitation_required"
            ),
        }
