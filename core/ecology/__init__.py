# ============================================
# NEXRYN ECOLOGY PACKAGE
# ============================================

from datetime import datetime

from core.ecology.adaptive_fitness_landscape import (
    AdaptiveFitnessLandscape,
)

from core.ecology.cognitive_niches import (
    CognitiveNiches,
)

from core.ecology.environmental_competition import (
    EnvironmentalCompetition,
)

from core.ecology.resource_pressure import (
    ResourcePressure,
)

from core.ecology.trait_selection import (
    TraitSelection,
)


class CognitiveEcology:

    def __init__(self):

        self.resource_pressure = ResourcePressure()
        self.cognitive_niches = CognitiveNiches()
        self.environmental_competition = (
            EnvironmentalCompetition()
        )
        self.trait_selection = TraitSelection()
        self.adaptive_fitness_landscape = (
            AdaptiveFitnessLandscape()
        )
        self.ecology_history = []

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        evolutionary = context.get(
            "evolutionary_memory_report",
            {},
        )

        resource_report = self.resource_pressure.compute(
            context,
        )

        niche_report = self.cognitive_niches.assign(
            evolutionary,
        )

        competition_report = (
            self.environmental_competition
            .compete(
                niche_report,
                resource_report,
            )
        )

        selection_report = self.trait_selection.select(
            competition_report,
        )

        landscape_report = self.adaptive_fitness_landscape.map(
            selection_report,
            resource_report,
        )

        report = {
            "system":
            "cognitive_ecology",

            "ecology_mode":
            "scarcity_competition_survival_pressure",

            "resource_pressure":
            resource_report,

            "cognitive_niches":
            niche_report,

            "environmental_competition":
            competition_report,

            "trait_selection":
            selection_report,

            "adaptive_fitness_landscape":
            landscape_report,

            "ecological_pressure_score":
            resource_report.get(
                "resource_pressure",
                0.0,
            ),

            "ecology_state":
            (
                "selection_under_scarcity"
                if selection_report.get(
                    "selected_count",
                    0,
                )
                else "awaiting_trait_competition"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.ecology_history.append(
            report,
        )

        self.ecology_history = (
            self.ecology_history[-128:]
        )

        return report


cognitive_ecology = (
    CognitiveEcology()
)


__all__ = [
    "AdaptiveFitnessLandscape",
    "CognitiveEcology",
    "CognitiveNiches",
    "EnvironmentalCompetition",
    "ResourcePressure",
    "TraitSelection",
    "cognitive_ecology",
]
