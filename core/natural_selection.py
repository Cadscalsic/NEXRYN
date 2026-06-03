# ============================================
# NEXRYN COGNITIVE NATURAL SELECTION
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


TRAIT_STATES = [
    "emerging",
    "candidate",
    "adaptive",
    "dominant",
    "decaying",
    "suppressed",
    "extinct",
]


class CognitiveNaturalSelection:

    def __init__(self):

        self.extinction_archive = []
        self.selection_history = []

    def _traits(self, context):

        return (
            context.get(
                "evolutionary_memory_report",
                {},
            )
            .get(
                "adaptive_trait_memory",
                {},
            )
            .get(
                "traits",
                [],
            )
        )

    def _resource_pressure(self, context):

        ecology = context.get(
            "cognitive_ecology_report",
            {},
        )

        return _clamp(
            ecology.get(
                "ecological_pressure_score",
                ecology.get(
                    "resource_pressure",
                    {},
                ).get(
                    "resource_pressure",
                    0.0,
                ),
            ),
        )

    def cognitive_resource_economy(self, trait, resource_pressure):

        mutation_rate = _clamp(
            trait.get(
                "mutation_rate",
                0.10,
            ),
        )

        fitness = _clamp(
            trait.get(
                "fitness",
                0.0,
            ),
        )

        observations = trait.get(
            "observations",
            len(
                trait.get(
                    "survival_history",
                    [],
                )
            ),
        )

        energy_cost = _clamp(
            0.08
            +
            mutation_rate * 0.28
            +
            resource_pressure * 0.18
        )

        memory_cost = _clamp(
            0.06
            +
            min(
                observations,
                24,
            )
            / 24
            * 0.18
        )

        attention_cost = _clamp(
            0.06
            +
            (
                1.0 - fitness
            )
            * 0.18
            +
            resource_pressure * 0.12
        )

        execution_cost = _clamp(
            0.05
            +
            mutation_rate * 0.22
        )

        maintenance_cost = _clamp(
            energy_cost * 0.30
            +
            memory_cost * 0.22
            +
            attention_cost * 0.28
            +
            execution_cost * 0.20
        )

        return {
            "energy_cost":
            energy_cost,

            "memory_cost":
            memory_cost,

            "attention_cost":
            attention_cost,

            "execution_cost":
            execution_cost,

            "maintenance_cost":
            maintenance_cost,
        }

    def fitness_after_costs(self, trait, resource_costs, context):

        utility = _clamp(
            trait.get(
                "fitness",
                0.0,
            )
            * 0.58
            +
            trait.get(
                "inheritance_strength",
                0.0,
            )
            * 0.22
            +
            trait.get(
                "semantic_alignment",
                0.0,
            )
            * 0.20
        )

        entropy_cost = _clamp(
            context.get(
                "runtime_entropy",
                0.0,
            )
            *
            trait.get(
                "mutation_rate",
                0.10,
            )
        )

        instability_cost = _clamp(
            1.0
            -
            trait.get(
                "stability_score",
                0.0,
            )
        )

        total_cost = _clamp(
            entropy_cost * 0.30
            +
            resource_costs.get(
                "energy_cost",
                0.0,
            )
            * 0.18
            +
            resource_costs.get(
                "memory_cost",
                0.0,
            )
            * 0.12
            +
            resource_costs.get(
                "attention_cost",
                0.0,
            )
            * 0.14
            +
            resource_costs.get(
                "execution_cost",
                0.0,
            )
            * 0.10
            +
            resource_costs.get(
                "maintenance_cost",
                0.0,
            )
            * 0.12
            +
            instability_cost * 0.14
        )

        net_fitness = _clamp(
            utility
            -
            total_cost,
            minimum=0.0,
        )

        return {
            "utility":
            utility,

            "entropy_cost":
            entropy_cost,

            "instability_cost":
            instability_cost,

            "total_cost":
            total_cost,

            "net_fitness":
            net_fitness,
        }

    def build_trait_competition_matrix(self, traits, context):

        resource_pressure = self._resource_pressure(
            context,
        )

        territories = {}
        matrix = []

        for trait in traits:

            territory = trait.get(
                "niche",
                "general_adaptation",
            )

            territories[
                territory
            ] = territories.get(
                territory,
                0,
            ) + 1

        for trait in traits:

            resource_costs = self.cognitive_resource_economy(
                trait,
                resource_pressure,
            )

            fitness_report = self.fitness_after_costs(
                trait,
                resource_costs,
                context,
            )

            territory = trait.get(
                "niche",
                "general_adaptation",
            )

            dominance_pressure = _clamp(
                (
                    territories.get(
                        territory,
                        1,
                    )
                    - 1
                )
                / 8
            )

            adaptive_advantage = _clamp(
                fitness_report.get(
                    "net_fitness",
                    0.0,
                )
                +
                trait.get(
                    "semantic_alignment",
                    0.0,
                )
                * 0.18
                +
                trait.get(
                    "stability_score",
                    0.0,
                )
                * 0.14
                -
                dominance_pressure * 0.20
            )

            competition_score = _clamp(
                adaptive_advantage * 0.54
                +
                fitness_report.get(
                    "net_fitness",
                    0.0,
                )
                * 0.28
                -
                resource_pressure * 0.18
            )

            matrix.append({
                "trait_id":
                trait.get(
                    "id",
                    trait.get(
                        "trait",
                        "unknown",
                    ),
                ),

                "semantic_territory":
                territory,

                "competition_score":
                competition_score,

                "resource_pressure":
                resource_pressure,

                "dominance_pressure":
                dominance_pressure,

                "adaptive_advantage":
                adaptive_advantage,

                "resource_costs":
                resource_costs,

                "fitness_report":
                fitness_report,
            })

        return matrix

    def classify_trait(self, trait, matrix_item):

        net_fitness = matrix_item.get(
            "fitness_report",
            {},
        ).get(
            "net_fitness",
            0.0,
        )

        competition_score = matrix_item.get(
            "competition_score",
            0.0,
        )

        history = trait.get(
            "survival_history",
            [],
        )

        repeated_failure = len([
            item
            for item in history[-4:]
            if item.get(
                "constructive_score",
                0.0,
            )
            < 0.24
        ])

        if repeated_failure >= 3 or net_fitness < 0.08:

            return "extinct"

        if competition_score < 0.16 or net_fitness < 0.16:

            return "suppressed"

        if competition_score < 0.28 or net_fitness < 0.26:

            return "decaying"

        if competition_score >= 0.72 and net_fitness >= 0.68:

            return "dominant"

        if competition_score >= 0.46 and net_fitness >= 0.42:

            return "adaptive"

        if history:

            return "candidate"

        return "emerging"

    def archive_trait(self, trait, reason):

        archived = {
            "trait_id":
            trait.get(
                "id",
                trait.get(
                    "trait",
                    "unknown",
                ),
            ),

            "reason":
            reason,

            "trait_snapshot":
            trait,

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.extinction_archive.append(
            archived,
        )

        self.extinction_archive = (
            self.extinction_archive[-256:]
        )

        return archived

    def suppress_trait(self, trait, matrix_item):

        return {
            "trait_id":
            matrix_item.get(
                "trait_id",
                "unknown",
            ),

            "action":
            "suppress_trait",

            "reason":
            "low_competition_score_or_high_cost",
        }

    def delete_trait(self, trait, matrix_item):

        return {
            "trait_id":
            matrix_item.get(
                "trait_id",
                "unknown",
            ),

            "action":
            "delete_trait",

            "reason":
            "extinct_trait_repeated_failure",
        }

    def trait_speciation(self, traits):

        species = {
            "preservation_species": [],
            "growth_species": [],
            "replication_species": [],
            "causal_species": [],
            "general_species": [],
        }

        for trait in traits:

            trait_id = str(
                trait.get(
                    "id",
                    trait.get(
                        "trait",
                        "unknown",
                    ),
                )
            )

            niche = str(
                trait.get(
                    "niche",
                    "",
                )
            )

            if "preserve" in trait_id or "identity" in niche:

                species[
                    "preservation_species"
                ].append(
                    trait_id,
                )

            elif "growth" in trait_id or "expand" in trait_id:

                species[
                    "growth_species"
                ].append(
                    trait_id,
                )

            elif "replication" in trait_id or "duplicate" in trait_id:

                species[
                    "replication_species"
                ].append(
                    trait_id,
                )

            elif "causal" in niche or "motion" in trait_id:

                species[
                    "causal_species"
                ].append(
                    trait_id,
                )

            else:

                species[
                    "general_species"
                ].append(
                    trait_id,
                )

        return {
            "trait_species":
            species,

            "species_count":
            len([
                items
                for items in species.values()
                if items
            ]),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        traits = self._traits(
            context,
        )

        matrix = self.build_trait_competition_matrix(
            traits,
            context,
        )

        selected_traits = []
        decaying_traits = []
        suppressed_traits = []
        extinct_traits = []
        actions = []
        archives = []

        by_id = {
            item.get(
                "trait_id",
            ):
            item
            for item in matrix
        }

        for trait in traits:

            trait_id = trait.get(
                "id",
                trait.get(
                    "trait",
                    "unknown",
                ),
            )

            matrix_item = by_id.get(
                trait_id,
                {},
            )

            state = self.classify_trait(
                trait,
                matrix_item,
            )

            updated = dict(
                trait,
            )

            updated[
                "trait_state"
            ] = state

            updated[
                "net_fitness"
            ] = matrix_item.get(
                "fitness_report",
                {},
            ).get(
                "net_fitness",
                0.0,
            )

            if state in [
                "dominant",
                "adaptive",
                "candidate",
            ]:

                selected_traits.append(
                    updated,
                )

            elif state == "decaying":

                decaying_traits.append(
                    updated,
                )

                actions.append(
                    self.archive_trait(
                        updated,
                        "decaying_trait_retained_for_observation",
                    )
                )

            elif state == "suppressed":

                suppressed_traits.append(
                    updated,
                )

                actions.append(
                    self.suppress_trait(
                        updated,
                        matrix_item,
                    )
                )

            elif state == "extinct":

                extinct_traits.append(
                    updated,
                )

                actions.append({
                    "trait_id":
                    trait_id,

                    "action":
                    "queue_extinction_pending_epistemic_trial",

                    "reason":
                    "natural_selection_recommends_extinction",
                })

            else:

                selected_traits.append(
                    updated,
                )

        speciation = self.trait_speciation(
            traits,
        )

        report = {
            "system":
            "cognitive_natural_selection",

            "selection_mode":
            "cognitive_death_competition_replacement",

            "trait_competition_matrix":
            matrix,

            "selected_traits":
            selected_traits,

            "decaying_traits":
            decaying_traits,

            "suppressed_traits":
            suppressed_traits,

            "extinct_traits":
            extinct_traits,

            "selection_actions":
            actions,

            "extinction_archive":
            self.extinction_archive[-32:],

            "pending_epistemic_trial_traits":
            [
                trait.get(
                    "id",
                    trait.get("trait", "unknown"),
                )
                for trait in extinct_traits
            ],

            "pending_epistemic_trial_count":
            len(
                extinct_traits,
            ),

            "trait_speciation":
            speciation,

            "selected_count":
            len(
                selected_traits,
            ),

            "decaying_count":
            len(
                decaying_traits,
            ),

            "suppressed_count":
            len(
                suppressed_traits,
            ),

            "extinct_count":
            len(
                extinct_traits,
            ),

            "selection_state":
            (
                "extinction_wave"
                if extinct_traits
                else "active_natural_selection"
                if suppressed_traits
                or decaying_traits
                else "selection_pressure_low"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.selection_history.append(
            report,
        )

        self.selection_history = (
            self.selection_history[-128:]
        )

        return report


cognitive_natural_selection = (
    CognitiveNaturalSelection()
)
