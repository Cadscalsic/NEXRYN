# ============================================
# NEXRYN COGNITIVE NICHES
# ============================================

from datetime import datetime


class CognitiveNiches:

    def assign(self, evolutionary_report):

        traits = evolutionary_report.get(
            "adaptive_trait_memory",
            {},
        ).get(
            "traits",
            [],
        )

        niches = []

        for trait in traits:

            name = str(
                trait.get(
                    "id",
                    trait.get(
                        "trait",
                        "unknown",
                    ),
                )
            )

            explicit_niche = trait.get(
                "niche",
            )

            if explicit_niche:

                niche = explicit_niche

            elif "identity" in name or "preserve" in name:

                niche = "identity_stability"

            elif "direction" in name or "position" in name:

                niche = "spatial_causal_reasoning"

            elif "symbolic" in name or "remap" in name:

                niche = "semantic_remapping"

            else:

                niche = "general_adaptation"

            niches.append({
                "trait":
                name,

                "niche":
                niche,

                "fitness":
                trait.get(
                    "fitness",
                    0.0,
                ),

                "mutation_rate":
                trait.get(
                    "mutation_rate",
                    0.0,
                ),

                "inheritance_strength":
                trait.get(
                    "inheritance_strength",
                    0.0,
                ),

                "stability_score":
                trait.get(
                    "stability_score",
                    0.0,
                ),

                "semantic_alignment":
                trait.get(
                    "semantic_alignment",
                    0.0,
                ),

                "observations":
                trait.get(
                    "observations",
                    0,
                ),
            })

        return {
            "system":
            "cognitive_niches",

            "niches":
            niches,

            "niche_count":
            len(
                {
                    item.get(
                        "niche",
                    )
                    for item in niches
                }
            ),

            "trait_count":
            len(
                niches,
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
