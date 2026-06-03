# ============================================
# NEXRYN CONCEPT BIRTH
# ============================================

from datetime import datetime

from core.concept_lifecycle.bridge_hallucination_filter import (
    BridgeHallucinationFilter,
)


class ConceptBirth:

    def __init__(self):

        self.bridge_hallucination_filter = (
            BridgeHallucinationFilter()
        )

    def collect_births(self, context):

        neurogenesis = context.get(
            "conceptive_neurogenesis_report",
            {},
        )

        concepts = neurogenesis.get(
            "generated_concepts",
            [],
        )

        filter_report = (
            self.bridge_hallucination_filter
            .filter(
                concepts,
                context,
            )
        )

        births = []

        for concept in filter_report.get(
            "accepted_concepts",
            [],
        ):

            name = concept.get(
                "concept",
                "unknown_concept",
            )

            births.append({
                "concept_id":
                f"concept:{name}",

                "concept":
                name,

                "origin":
                concept.get(
                    "origin",
                    "unknown",
                ),

                "viability":
                concept.get(
                    "viability",
                    0.0,
                ),

                "state":
                "born",

                "born_at":
                str(
                    datetime.utcnow()
                ),
            })

        return {
            "system":
            "concept_birth",

            "births":
            births,

            "birth_count":
            len(
                births,
            ),

            "bridge_hallucination_filter":
            filter_report,
        }
