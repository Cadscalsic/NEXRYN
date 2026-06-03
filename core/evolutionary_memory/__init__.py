# ============================================
# NEXRYN EVOLUTIONARY MEMORY PACKAGE
# ============================================

from datetime import datetime

from core.evolutionary_memory.adaptive_trait_memory import (
    AdaptiveTraitMemory,
    CognitiveTrait,
)

from core.evolutionary_memory.beneficial_pattern_archive import (
    BeneficialPatternArchive,
)

from core.evolutionary_memory.cognitive_genealogy import (
    CognitiveGenealogy,
)

from core.evolutionary_memory.evolutionary_pressure import (
    EvolutionaryPressure,
)

from core.evolutionary_memory.mutation_lineage import (
    MutationLineage,
)


class EvolutionaryMemory:

    def __init__(self):

        self.mutation_lineage = MutationLineage()
        self.beneficial_pattern_archive = (
            BeneficialPatternArchive()
        )
        self.cognitive_genealogy = CognitiveGenealogy()
        self.adaptive_trait_memory = AdaptiveTraitMemory()
        self.evolutionary_pressure = EvolutionaryPressure()
        self.memory_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        lineage_report = self.mutation_lineage.track(
            context,
        )

        archive_report = (
            self.beneficial_pattern_archive
            .archive_patterns(lineage_report)
        )

        genealogy_report = self.cognitive_genealogy.update(
            lineage_report,
            archive_report,
        )

        trait_report = self.adaptive_trait_memory.update(
            archive_report,
        )

        pressure_report = self.evolutionary_pressure.compute(
            lineage_report,
            archive_report,
            trait_report,
            context,
        )

        report = {
            "system":
            "evolutionary_memory",

            "memory_mode":
            "persistent_cognitive_mutation_memory",

            "mutation_lineage":
            lineage_report,

            "beneficial_pattern_archive":
            archive_report,

            "cognitive_genealogy":
            genealogy_report,

            "adaptive_trait_memory":
            trait_report,

            "evolutionary_pressure":
            pressure_report,

            "heredity_state":
            (
                "adaptive_heredity_forming"
                if archive_report.get(
                    "archive_size",
                    0,
                )
                or trait_report.get(
                    "trait_count",
                    0,
                )
                else "awaiting_surviving_mutations"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.memory_history.append(
            report,
        )

        self.memory_history = (
            self.memory_history[-128:]
        )

        return report


evolutionary_memory = (
    EvolutionaryMemory()
)


__all__ = [
    "AdaptiveTraitMemory",
    "BeneficialPatternArchive",
    "CognitiveTrait",
    "CognitiveGenealogy",
    "EvolutionaryMemory",
    "EvolutionaryPressure",
    "MutationLineage",
    "evolutionary_memory",
]
