# =========================================================
# NEXRYN RECURSIVE COGNITIVE GENETICS
# =========================================================

from datetime import datetime
from dataclasses import dataclass, field

import uuid
import random
import copy


# =========================================================
# COGNITIVE DNA
# =========================================================

@dataclass
class CognitiveDNA:

    genome_id: str

    reasoning_type: str

    abstraction_capacity: float

    recursive_depth: int

    adaptation_rate: float

    mutation_resistance: float

    semantic_alignment: float

    fitness_score: float

    generation: int = 1

    mutations: list = field(
        default_factory=list
    )

    ancestry: list = field(
        default_factory=list
    )

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# COGNITIVE GENOME
# =========================================================

class CognitiveGenome:

    # =====================================================
    # INITIALIZE GENOME
    # =====================================================

    def __init__(self):

        self.genome_memory = []

        self.trait_evolution = []

        self.lineage_history = []

        self.active_genomes = []

        self.extinct_genomes = []

        self.mutation_history = []

        self.genetic_archive = []

        # =================================================
        # GENOME STATE
        # =================================================

        self.genome_state = {

            "genome_mode":
            "recursive_cognitive_genetics",

            "cognitive_species":
            "recursive_executive",

            "adaptation_level":
            "high",

            "genome_stability":
            "stable",

            "evolution_cycles":
            0,

            "dominant_trait":
            None,

            "genetic_complexity":
            "advanced",

            "mutation_engine":
            "active",

            "genetic_selection":
            "enabled",

            "cognitive_heritability":
            "enabled"
        }

    # =====================================================
    # CREATE GENOME
    # =====================================================

    def create_genome(

        self,

        cognitive_traits
    ):

        genome = CognitiveDNA(

            genome_id=str(uuid.uuid4()),

            reasoning_type=

            cognitive_traits.get(
                "dominant_reasoning",
                "general_reasoning"
            ),

            abstraction_capacity=round(
                random.uniform(0.5, 1.0),
                2
            ),

            recursive_depth=

            cognitive_traits.get(
                "reasoning_depth",
                1
            ),

            adaptation_rate=round(
                random.uniform(0.5, 1.0),
                2
            ),

            mutation_resistance=round(
                random.uniform(0.5, 1.0),
                2
            ),

            semantic_alignment=round(
                random.uniform(0.5, 1.0),
                2
            ),

            fitness_score=round(
                random.uniform(0.5, 1.0),
                2
            )
        )

        self.active_genomes.append(
            genome
        )

        return genome

    # =====================================================
    # EXTRACT COGNITIVE TRAITS
    # =====================================================

    def extract_cognitive_traits(

        self,

        runtime_context
    ):

        identity_state = (

            runtime_context.get(
                "identity_report",
                {}
            ).get(
                "identity_state",
                {}
            )
        )

        recursive_report = (

            runtime_context.get(
                "recursive_report",
                {}
            )
        )

        inference_report = (

            runtime_context.get(
                "inference_report",
                {}
            )
        )

        trajectory_score = (

            runtime_context.get(
                "trajectory_score",
                {}
            )
        )

        traits = {

            "dominant_reasoning":

            recursive_report.get(
                "dominant_reasoning"
            ),

            "dominant_strategy":

            identity_state.get(
                "dominant_strategy"
            ),

            "reasoning_depth":

            inference_report.get(
                "reasoning_depth",
                0
            ),

            "cognitive_complexity":

            recursive_report.get(
                "cognitive_complexity"
            ),

            "semantic_alignment":

            identity_state.get(
                "semantic_alignment"
            ),

            "trajectory_quality":

            trajectory_score.get(
                "trajectory_quality"
            ),

            "genome_state":
            "adaptive_recursive",

            "timestamp":
            str(datetime.utcnow())
        }

        self.genome_memory.append(
            traits
        )

        return traits

    # =====================================================
    # MUTATE GENOMES
    # =====================================================

    def mutate_genomes(self):

        mutations = []

        for genome in self.active_genomes:

            mutation_probability = random.random()

            if mutation_probability < 0.15:

                mutation = random.choice([

                    "recursive_depth_expansion",

                    "semantic_alignment_boost",

                    "adaptive_reasoning_shift",

                    "symbolic_compression"
                ])

                genome.mutations.append(
                    mutation
                )

                genome.adaptation_rate = round(

                    min(
                        genome.adaptation_rate + 0.05,
                        1.0
                    ),

                    2
                )

                mutations.append({

                    "genome":
                    genome.genome_id,

                    "mutation":
                    mutation
                })

        self.mutation_history.extend(
            mutations
        )

        return mutations

    # =====================================================
    # RECOMBINE GENOMES
    # =====================================================

    def recombine_genomes(self):

        offspring = []

        if len(self.active_genomes) < 2:

            return offspring

        shuffled = copy.copy(
            self.active_genomes
        )

        random.shuffle(shuffled)

        for i in range(

            0,

            len(shuffled) - 1,

            2
        ):

            parent_a = shuffled[i]

            parent_b = shuffled[i + 1]

            child = CognitiveDNA(

                genome_id=str(uuid.uuid4()),

                reasoning_type=random.choice([

                    parent_a.reasoning_type,

                    parent_b.reasoning_type
                ]),

                abstraction_capacity=round(

                    (
                        parent_a.abstraction_capacity
                        +
                        parent_b.abstraction_capacity
                    ) / 2,

                    2
                ),

                recursive_depth=max(

                    parent_a.recursive_depth,

                    parent_b.recursive_depth
                ),

                adaptation_rate=round(

                    (
                        parent_a.adaptation_rate
                        +
                        parent_b.adaptation_rate
                    ) / 2,

                    2
                ),

                mutation_resistance=round(

                    (
                        parent_a.mutation_resistance
                        +
                        parent_b.mutation_resistance
                    ) / 2,

                    2
                ),

                semantic_alignment=round(

                    (
                        parent_a.semantic_alignment
                        +
                        parent_b.semantic_alignment
                    ) / 2,

                    2
                ),

                fitness_score=round(

                    (
                        parent_a.fitness_score
                        +
                        parent_b.fitness_score
                    ) / 2,

                    2
                ),

                generation=max(

                    parent_a.generation,

                    parent_b.generation
                ) + 1,

                ancestry=[

                    parent_a.genome_id,

                    parent_b.genome_id
                ]
            )

            offspring.append(child)

        self.active_genomes.extend(
            offspring
        )

        return offspring

    # =====================================================
    # SELECT FITTEST GENOMES
    # =====================================================

    def select_fittest_genomes(self):

        survivors = []

        extinct = []

        for genome in self.active_genomes:

            if genome.fitness_score < 0.45:

                extinct.append(genome)

            else:

                survivors.append(genome)

        self.extinct_genomes.extend(
            extinct
        )

        self.active_genomes = survivors

        return survivors

    # =====================================================
    # BUILD LINEAGE
    # =====================================================

    def build_lineage(

        self,

        genome
    ):

        lineage = {

            "lineage_id":

            len(
                self.lineage_history
            ) + 1,

            "genome":
            genome.genome_id,

            "reasoning_type":
            genome.reasoning_type,

            "generation":
            genome.generation,

            "ancestry":
            genome.ancestry,

            "evolution_depth":

            self.genome_state.get(
                "evolution_cycles"
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.lineage_history.append(
            lineage
        )

        return lineage

    # =====================================================
    # EXPRESS PHENOTYPE
    # =====================================================

    def express_cognitive_phenotype(

        self,

        genome
    ):

        phenotype = {

            "reasoning_style":
            genome.reasoning_type,

            "symbolic_capacity":

            "advanced"

            if genome.abstraction_capacity >= 0.85

            else "moderate",

            "recursive_behavior":

            "deep"

            if genome.recursive_depth >= 10

            else "moderate",

            "adaptation_behavior":

            "high"

            if genome.adaptation_rate >= 0.85

            else "stable",

            "cognitive_fitness":
            genome.fitness_score,

            "generation":
            genome.generation
        }

        return phenotype

    # =====================================================
    # EVOLVE TRAITS
    # =====================================================

    def evolve_traits(

        self,

        trajectory_score
    ):

        score = trajectory_score.get(
            "trajectory_score",
            0.0
        )

        evolution = {

            "evolution_score":
            score,

            "evolution_result":

            "advanced_evolution"

            if score >= 0.90

            else "moderate_evolution",

            "genetic_shift":

            "high"

            if score >= 0.95

            else "moderate",

            "timestamp":
            str(datetime.utcnow())
        }

        self.trait_evolution.append(
            evolution
        )

        self.genome_state[
            "evolution_cycles"
        ] += 1

        return evolution

    # =====================================================
    # RUN GENOME CYCLE
    # =====================================================

    def run_genome_cycle(

        self,

        runtime_context,

        trajectory_score
    ):

        traits = (

            self.extract_cognitive_traits(
                runtime_context
            )
        )

        genome = (
            self.create_genome(
                traits
            )
        )

        mutations = (
            self.mutate_genomes()
        )

        offspring = (
            self.recombine_genomes()
        )

        survivors = (
            self.select_fittest_genomes()
        )

        lineage = (
            self.build_lineage(
                genome
            )
        )

        phenotype = (

            self.express_cognitive_phenotype(
                genome
            )
        )

        evolution = (

            self.evolve_traits(
                trajectory_score
            )
        )

        report = {

            "genome":
            genome,

            "mutations":
            len(mutations),

            "offspring":
            len(offspring),

            "survivors":
            len(survivors),

            "lineage":
            lineage,

            "phenotype":
            phenotype,

            "evolution":
            evolution,

            "timestamp":
            str(datetime.utcnow())
        }

        self.genetic_archive.append(
            report
        )

        return report

    # =====================================================
    # BUILD GENOME REPORT
    # =====================================================

    def build_genome_report(self):

        return {

            "genome_state":
            self.genome_state,

            "active_genomes":
            len(self.active_genomes),

            "extinct_genomes":
            len(self.extinct_genomes),

            "mutation_events":
            len(self.mutation_history),

            "lineage_depth":
            len(self.lineage_history),

            "genetic_archive":
            len(self.genetic_archive),

            "latest_genome":

            self.genetic_archive[-1]

            if self.genetic_archive

            else {}
        }