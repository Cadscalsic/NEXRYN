# ============================================
# NEXRYN SEMANTIC ANTIBODIES
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class SemanticAntibodySystem:

    def detect_semantic_infection(self, context):

        ontology = context.get(
            "ontology_defragmenter_report",
            {},
        )

        fragmentation = ontology.get(
            "semantic_fragmentation_before",
            context.get(
                "semantic_fragmentation",
                0.0,
            ),
        )

        fusion = context.get(
            "adaptive_semantic_compression_report",
            {},
        )

        risky_fusions = len(
            fusion.get(
                "fold_candidates",
                [],
            )
        )

        infection_score = _clamp(
            fragmentation * 0.65
            +
            min(
                risky_fusions,
                12,
            )
            / 12
            * 0.35
        )

        return {
            "semantic_infection_score":
            infection_score,

            "infection_state":
            (
                "infected"
                if infection_score >= 0.68
                else "watch"
                if infection_score >= 0.45
                else "clean"
            ),
        }

    def generate_antibodies(self, context):

        infection = self.detect_semantic_infection(
            context,
        )

        antibodies = []

        if infection.get(
            "semantic_infection_score",
            0.0,
        ) >= 0.45:

            antibodies.extend([
                {
                    "antibody":
                    "block_unstable_concept_fusion",

                    "targets":
                    [
                        "unstable_concept_fusion",
                        "unsafe_merge",
                    ],
                },
                {
                    "antibody":
                    "quarantine_orphan_semantics",

                    "targets":
                    [
                        "orphan_concepts",
                        "stale_semantic_routes",
                    ],
                },
            ])

        if infection.get(
            "semantic_infection_score",
            0.0,
        ) >= 0.68:

            antibodies.append({
                "antibody":
                "freeze_ontology_mutation",

                "targets":
                [
                    "ontology_collapse",
                    "semantic_fragmentation",
                ],
            })

        return {
            "system":
            "semantic_antibody_system",

            "infection":
            infection,

            "antibodies":
            antibodies,

            "antibody_count":
            len(
                antibodies,
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
