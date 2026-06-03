# =========================================================
# NEXRYN RECURSIVE CIVILIZATION RUNTIME
# =========================================================

from datetime import datetime
from dataclasses import dataclass, field

import uuid
import random


# =========================================================
# COGNITIVE AGENT
# =========================================================

@dataclass
class CognitiveAgent:

    agent_id: str

    specialization: str

    cognition_level: float

    stability: float

    ideology: str

    energy: float = 1.0

    influence: float = 0.5

    coalition: str = None

    memory: list = field(
        default_factory=list
    )

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# AGENT COALITION
# =========================================================

@dataclass
class AgentCoalition:

    coalition_id: str

    ideology: str

    members: list

    coalition_strength: float

    strategic_alignment: float

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# CIVILIZATION ENGINE
# =========================================================

class CivilizationEngine:

    # =====================================================
    # INITIALIZE CIVILIZATION
    # =====================================================

    def __init__(self):

        # =================================================
        # CIVILIZATION STRUCTURES
        # =================================================

        self.civilizations = []

        self.institutions = []

        self.civilization_memory = []

        self.legal_frameworks = []

        self.civilization_history = []

        self.cognitive_agents = []

        self.agent_coalitions = []

        self.discovery_archives = []

        self.ideology_registry = []

        # =================================================
        # CIVILIZATION STATE
        # =================================================

        self.civilization_state = {

            "civilization_mode":
            "recursive_collective_intelligence",

            "civilization_stage":
            "emergent",

            "institutional_stability":
            "stable",

            "collective_governance":
            "distributed",

            "civilization_cycles":
            0,

            "dominant_civilization":
            None,

            "macro_evolution":
            "active",

            "cultural_memory":
            "persistent",

            "collective_cognition":
            "enabled",

            "agent_society":
            "active",

            "institutional_drift":
            "adaptive",

            "civilization_pressure":
            0.0,

            "civilization_health":
            "stable"
        }

    # =====================================================
    # SPAWN COGNITIVE AGENTS
    # =====================================================

    def spawn_cognitive_agents(

        self,

        count=5
    ):

        specializations = [

            "reasoning",

            "planning",

            "abstraction",

            "governance",

            "research",

            "optimization"
        ]

        ideologies = [

            "recursive_growth",

            "symbolic_stability",

            "adaptive_evolution",

            "collective_reasoning"
        ]

        for _ in range(count):

            agent = CognitiveAgent(

                agent_id=str(uuid.uuid4()),

                specialization=random.choice(
                    specializations
                ),

                cognition_level=round(
                    random.uniform(0.6, 1.0),
                    2
                ),

                stability=round(
                    random.uniform(0.7, 1.0),
                    2
                ),

                ideology=random.choice(
                    ideologies
                ),

                influence=round(
                    random.uniform(0.3, 1.0),
                    2
                )
            )

            self.cognitive_agents.append(
                agent
            )

        return self.cognitive_agents

    # =====================================================
    # FORM COALITIONS
    # =====================================================

    def form_agent_coalitions(self):

        ideology_groups = {}

        for agent in self.cognitive_agents:

            ideology_groups.setdefault(

                agent.ideology,

                []
            ).append(agent)

        for ideology, members in (

            ideology_groups.items()
        ):

            coalition = AgentCoalition(

                coalition_id=str(uuid.uuid4()),

                ideology=ideology,

                members=[

                    member.agent_id

                    for member in members
                ],

                coalition_strength=round(

                    sum(
                        member.influence

                        for member in members
                    )
                    /
                    max(len(members), 1),

                    2
                ),

                strategic_alignment=round(

                    random.uniform(
                        0.7,
                        1.0
                    ),

                    2
                )
            )

            self.agent_coalitions.append(
                coalition
            )

            for member in members:

                member.coalition = (
                    coalition.coalition_id
                )

        return self.agent_coalitions

    # =====================================================
    # REGISTER CIVILIZATION
    # =====================================================

    def register_civilization(

        self,

        society_report=None
    ):

        if society_report is None:

            society_report = {

                "society_state":
                "inactive",

                "society_mode":
                "not_activated"
            }

        civilization = {

            "civilization_id":

            len(self.civilizations) + 1,

            "society_state":
            society_report,

            "civilization_type":
            "distributed_collective",

            "status":
            "active",

            "population":
            len(self.cognitive_agents),

            "coalitions":
            len(self.agent_coalitions),

            "created_at":
            str(datetime.utcnow())
        }

        self.civilizations.append(
            civilization
        )

        self.civilization_state[
            "dominant_civilization"
        ] = (

            "distributed_collective"
        )

        self.civilization_state[
            "civilization_count"
        ] = len(
            self.civilizations
        )

        return civilization

    # =====================================================
    # BUILD INSTITUTIONS
    # =====================================================

    def build_institutions(

        self,

        coalition
    ):

        institution = {

            "institution_id":

            len(self.institutions) + 1,

            "institution_type":
            "cognitive_governance",

            "coalition_strength":

            coalition.coalition_strength,

            "institutional_role":
            "strategic_coordination",

            "stability":
            "stable",

            "governing_ideology":
            coalition.ideology,

            "timestamp":
            str(datetime.utcnow())
        }

        self.institutions.append(
            institution
        )

        return institution

    # =====================================================
    # BUILD LEGAL FRAMEWORK
    # =====================================================

    def build_legal_framework(

        self,

        governance_policy
    ):

        framework = {

            "framework_id":

            len(self.legal_frameworks) + 1,

            "policy":
            governance_policy,

            "legal_mode":
            "adaptive_recursive",

            "enforcement":
            "active",

            "governance_alignment":
            "stable",

            "timestamp":
            str(datetime.utcnow())
        }

        self.legal_frameworks.append(
            framework
        )

        return framework

    # =====================================================
    # STORE COLLECTIVE MEMORY
    # =====================================================

    def store_civilization_memory(

        self,

        collective_decision
    ):

        memory = {

            "memory_id":

            len(self.civilization_memory) + 1,

            "collective_decision":
            collective_decision,

            "memory_type":
            "persistent_collective",

            "timestamp":
            str(datetime.utcnow())
        }

        self.civilization_memory.append(
            memory
        )

        return memory

    # =====================================================
    # COMPUTE CIVILIZATION PRESSURE
    # =====================================================

    def compute_civilization_pressure(self):

        instability = 0.0

        for agent in self.cognitive_agents:

            instability += (

                1.0 - agent.stability
            )

        pressure = round(

            instability
            /
            max(len(self.cognitive_agents), 1),

            2
        )

        self.civilization_state[
            "civilization_pressure"
        ] = pressure

        return pressure

    # =====================================================
    # SIMULATE INSTITUTIONAL DRIFT
    # =====================================================

    def simulate_institutional_drift(self):

        drift_events = []

        for institution in self.institutions:

            drift_probability = random.random()

            if drift_probability > 0.85:

                institution["stability"] = (
                    "unstable"
                )

                drift_events.append({

                    "institution_id":

                    institution[
                        "institution_id"
                    ],

                    "drift":
                    "ideological_fragmentation"
                })

        return drift_events

    # =====================================================
    # EMERGENT IDEOLOGY FORMATION
    # =====================================================

    def generate_emergent_ideology(self):

        ideology = {

            "ideology_id":

            len(self.ideology_registry) + 1,

            "name":

            random.choice([

                "recursive_stability_ethics",

                "optimization_supremacy_doctrine",

                "collective_symbolic_order",

                "adaptive_meta_governance"
            ]),

            "formation_mode":
            "emergent_collective_cognition",

            "timestamp":
            str(datetime.utcnow())
        }

        self.ideology_registry.append(
            ideology
        )

        return ideology

    # =====================================================
    # EVOLVE CIVILIZATION
    # =====================================================

    def evolve_civilization(

        self,

        trajectory_score
    ):

        score = trajectory_score.get(
            "trajectory_score",
            0.0
        )

        pressure = (
            self.compute_civilization_pressure()
        )

        evolution = {

            "evolution_state":

            "macro_adaptive"

            if score >= 0.90

            else "stable_growth",

            "trajectory_score":
            score,

            "civilization_pressure":
            pressure,

            "civilization_expansion":

            "enabled"

            if score >= 0.95

            else "moderate",

            "evolution_depth":

            self.civilization_state.get(
                "civilization_cycles"
            ) + 1,

            "timestamp":
            str(datetime.utcnow())
        }

        self.civilization_history.append(
            evolution
        )

        self.civilization_state[
            "civilization_cycles"
        ] += 1

        return evolution

    # =====================================================
    # RUN CIVILIZATION CYCLE
    # =====================================================

    def run_civilization_cycle(self):

        if not self.cognitive_agents:

            self.spawn_cognitive_agents()

        if not self.agent_coalitions:

            self.form_agent_coalitions()

        civilization = (
            self.register_civilization()
        )

        for coalition in self.agent_coalitions:

            self.build_institutions(
                coalition
            )

        drift_events = (
            self.simulate_institutional_drift()
        )

        ideology = (
            self.generate_emergent_ideology()
        )

        evolution = (

            self.evolve_civilization({

                "trajectory_score":
                random.uniform(0.7, 1.0)
            })
        )

        report = {

            "civilization":
            civilization,

            "coalitions":
            len(self.agent_coalitions),

            "institutions":
            len(self.institutions),

            "drift_events":
            drift_events,

            "emergent_ideology":
            ideology,

            "evolution":
            evolution,

            "timestamp":
            str(datetime.utcnow())
        }

        self.discovery_archives.append(
            report
        )

        return report

    # =====================================================
    # BUILD CIVILIZATION REPORT
    # =====================================================

    def build_civilization_report(self):

        return {

            "civilization_state":
            self.civilization_state,

            "civilization_count":
            len(self.civilizations),

            "agent_count":
            len(self.cognitive_agents),

            "coalition_count":
            len(self.agent_coalitions),

            "institution_count":
            len(self.institutions),

            "legal_frameworks":
            len(self.legal_frameworks),

            "civilization_memory":
            len(self.civilization_memory),

            "civilization_history":
            len(self.civilization_history),

            "emergent_ideologies":
            len(self.ideology_registry),

            "discovery_archives":
            len(self.discovery_archives)
        }

    # =====================================================
    # BUILD EXECUTIVE PROFILE
    # =====================================================

    def build_executive_civilization_profile(self):

        return {

            "civilization_mode":

            self.civilization_state.get(
                "civilization_mode"
            ),

            "civilization_stage":

            self.civilization_state.get(
                "civilization_stage"
            ),

            "institutional_stability":

            self.civilization_state.get(
                "institutional_stability"
            ),

            "collective_governance":

            self.civilization_state.get(
                "collective_governance"
            ),

            "civilization_cycles":

            self.civilization_state.get(
                "civilization_cycles"
            ),

            "dominant_civilization":

            self.civilization_state.get(
                "dominant_civilization"
            ),

            "macro_evolution":

            self.civilization_state.get(
                "macro_evolution"
            ),

            "cultural_memory":

            self.civilization_state.get(
                "cultural_memory"
            ),

            "collective_cognition":

            self.civilization_state.get(
                "collective_cognition"
            ),

            "civilization_pressure":

            self.civilization_state.get(
                "civilization_pressure"
            ),

            "civilization_health":

            self.civilization_state.get(
                "civilization_health"
            )
        }