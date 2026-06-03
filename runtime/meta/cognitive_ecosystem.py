# =========================================================
# NEXRYN EVOLUTIONARY COGNITIVE ECOLOGY
# =========================================================

from datetime import datetime
from dataclasses import dataclass, field

import uuid
import random


# =========================================================
# ECOLOGICAL AGENT
# =========================================================

@dataclass
class EcologicalAgent:

    agent_id: str

    specialization: str

    reasoning_type: str

    fitness: float

    adaptability: float

    cooperation_score: float

    energy: float

    generation: int = 1

    mutations: list = field(
        default_factory=list
    )

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# COGNITIVE ECOSYSTEM
# =========================================================

class CognitiveEcosystem:

    # =====================================================
    # INITIALIZE ECOSYSTEM
    # =====================================================

    def __init__(self):

        self.cognitive_agents = []

        self.specialized_agents = []

        self.strategy_ecology = []

        self.ecosystem_history = []

        self.extinct_agents = []

        self.mutation_history = []

        self.ecological_memory = []

        # =================================================
        # ECOSYSTEM STATE
        # =================================================

        self.ecosystem_state = {

            "ecosystem_mode":
            "evolutionary_cognitive_ecology",

            "ecosystem_stability":
            "stable",

            "active_agents":
            0,

            "dominant_species":
            None,

            "evolutionary_pressure":
            "moderate",

            "ecosystem_cycles":
            0,

            "cooperation_level":
            "high",

            "competitive_pressure":
            "moderate",

            "mutation_rate":
            0.15,

            "extinction_pressure":
            "active",

            "adaptive_selection":
            "enabled"
        }

    # =====================================================
    # SPAWN AGENT
    # =====================================================

    def register_agent(

        self,

        specialization,

        reasoning_type,

        fitness
    ):

        agent = EcologicalAgent(

            agent_id=str(uuid.uuid4()),

            specialization=specialization,

            reasoning_type=reasoning_type,

            fitness=fitness,

            adaptability=round(
                random.uniform(0.5, 1.0),
                2
            ),

            cooperation_score=round(
                random.uniform(0.5, 1.0),
                2
            ),

            energy=round(
                random.uniform(0.5, 1.0),
                2
            )
        )

        self.cognitive_agents.append(
            agent
        )

        self.ecosystem_state[
            "active_agents"
        ] = len(
            self.cognitive_agents
        )

        return agent

    # =====================================================
    # BUILD STRATEGY ECOLOGY
    # =====================================================

    def build_strategy_ecology(

        self,

        evolved_hypotheses
    ):

        ecology = {

            "strategy_count":
            len(evolved_hypotheses),

            "strategies":
            evolved_hypotheses,

            "ecology_state":
            "competitive_adaptive",

            "selection_pressure":
            "active",

            "timestamp":
            str(datetime.utcnow())
        }

        self.strategy_ecology.append(
            ecology
        )

        return ecology

    # =====================================================
    # MUTATE AGENTS
    # =====================================================

    def mutate_agents(self):

        mutations = []

        for agent in self.cognitive_agents:

            mutation_probability = random.random()

            if mutation_probability < 0.15:

                mutation = random.choice([

                    "recursive_reasoning_boost",

                    "symbolic_compression",

                    "adaptive_search_expansion",

                    "cooperative_alignment"
                ])

                agent.mutations.append(
                    mutation
                )

                agent.adaptability = round(

                    min(
                        agent.adaptability + 0.05,
                        1.0
                    ),

                    2
                )

                mutations.append({

                    "agent":
                    agent.agent_id,

                    "mutation":
                    mutation
                })

        self.mutation_history.extend(
            mutations
        )

        return mutations

    # =====================================================
    # EVOLVE SPECIALIZED AGENTS
    # =====================================================

    def evolve_specialized_agents(

        self,

        semantic_graph
    ):

        specialized = []

        concepts = semantic_graph.get(
            "concept_nodes",
            []
        )

        for concept in concepts:

            agent = {

                "specialization":

                concept.get(
                    "concept"
                ),

                "confidence":

                concept.get(
                    "confidence",
                    0.0
                ),

                "evolution_state":
                "specialized",

                "timestamp":
                str(datetime.utcnow())
            }

            specialized.append(
                agent
            )

        self.specialized_agents.extend(
            specialized
        )

        return specialized

    # =====================================================
    # REPRODUCE AGENTS
    # =====================================================

    def reproduce_agents(self):

        offspring = []

        strong_agents = [

            agent

            for agent in self.cognitive_agents

            if agent.fitness >= 0.8
        ]

        for parent in strong_agents:

            child = EcologicalAgent(

                agent_id=str(uuid.uuid4()),

                specialization=
                parent.specialization,

                reasoning_type=
                parent.reasoning_type,

                fitness=round(

                    min(
                        parent.fitness
                        +
                        random.uniform(
                            -0.1,
                            0.1
                        ),
                        1.0
                    ),

                    2
                ),

                adaptability=parent.adaptability,

                cooperation_score=
                parent.cooperation_score,

                energy=1.0,

                generation=
                parent.generation + 1
            )

            offspring.append(child)

        self.cognitive_agents.extend(
            offspring
        )

        return offspring

    # =====================================================
    # EXTINCTION EVENTS
    # =====================================================

    def simulate_extinction(self):

        survivors = []

        extinct = []

        for agent in self.cognitive_agents:

            if agent.energy < 0.25:

                extinct.append(agent)

            else:

                survivors.append(agent)

        self.extinct_agents.extend(
            extinct
        )

        self.cognitive_agents = survivors

        return extinct

    # =====================================================
    # COMPUTE ECOSYSTEM BALANCE
    # =====================================================

    def compute_ecosystem_balance(

        self,

        trajectory_score
    ):

        score = trajectory_score.get(
            "trajectory_score",
            0.0
        )

        balance = {

            "ecosystem_balance":

            "stable"

            if score >= 0.90

            else "adaptive",

            "cooperation_strength":

            "high"

            if score >= 0.95

            else "moderate",

            "competitive_pressure":

            self.ecosystem_state.get(
                "competitive_pressure"
            ),

            "adaptive_selection":
            "active",

            "timestamp":
            str(datetime.utcnow())
        }

        self.ecosystem_history.append(
            balance
        )

        self.ecosystem_state[
            "ecosystem_cycles"
        ] += 1

        return balance

    # =====================================================
    # SELECT DOMINANT SPECIES
    # =====================================================

    def select_dominant_species(self):

        if not self.cognitive_agents:

            return None

        dominant = max(

            self.cognitive_agents,

            key=lambda agent:
            agent.fitness
        )

        self.ecosystem_state[
            "dominant_species"
        ] = dominant.reasoning_type

        return {

            "dominant_species":
            dominant.reasoning_type,

            "fitness":
            dominant.fitness,

            "selection_mode":
            "evolutionary_adaptive",

            "timestamp":
            str(datetime.utcnow())
        }

    # =====================================================
    # RUN ECOSYSTEM CYCLE
    # =====================================================

    def run_ecosystem_cycle(

        self,

        semantic_graph,

        evolved_hypotheses,

        trajectory_score
    ):

        self.build_strategy_ecology(
            evolved_hypotheses
        )

        self.evolve_specialized_agents(
            semantic_graph
        )

        mutations = (
            self.mutate_agents()
        )

        offspring = (
            self.reproduce_agents()
        )

        extinct = (
            self.simulate_extinction()
        )

        balance = (

            self.compute_ecosystem_balance(
                trajectory_score
            )
        )

        dominant = (
            self.select_dominant_species()
        )

        report = {

            "mutations":
            len(mutations),

            "offspring":
            len(offspring),

            "extinct":
            len(extinct),

            "dominant_species":
            dominant,

            "ecosystem_balance":
            balance,

            "timestamp":
            str(datetime.utcnow())
        }

        self.ecological_memory.append(
            report
        )

        return report

    # =====================================================
    # BUILD ECOSYSTEM REPORT
    # =====================================================

    def build_ecosystem_report(self):

        return {

            "ecosystem_state":
            self.ecosystem_state,

            "active_agents":
            len(self.cognitive_agents),

            "specialized_agents":
            len(self.specialized_agents),

            "strategy_ecologies":
            len(self.strategy_ecology),

            "ecosystem_history":
            len(self.ecosystem_history),

            "mutation_history":
            len(self.mutation_history),

            "extinct_agents":
            len(self.extinct_agents),

            "ecological_memory":
            len(self.ecological_memory)
        }