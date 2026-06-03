# =========================================================
# NEXRYN DISTRIBUTED COGNITIVE SOCIETY
# =========================================================

from datetime import datetime
from dataclasses import dataclass, field

import uuid
import random


# =========================================================
# SOCIETY MEMBER
# =========================================================

@dataclass
class SocietyMember:

    member_id: str

    specialization: str

    ideology: str

    reasoning_confidence: float

    influence: float

    trust_score: float

    reputation: float

    energy: float

    coalition: str = None

    memory: list = field(
        default_factory=list
    )

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# NEGOTIATION EVENT
# =========================================================

@dataclass
class NegotiationEvent:

    negotiation_id: str

    participants: list

    dominant_ideology: str

    consensus_score: float

    negotiation_pressure: float

    outcome: str

    timestamp: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# COGNITIVE SOCIETY
# =========================================================

class CognitiveSociety:

    # =====================================================
    # INITIALIZE SOCIETY
    # =====================================================

    def __init__(self):

        self.cognitive_members = []

        self.negotiation_history = []

        self.coalition_history = []

        self.collective_decisions = []

        self.shared_memory = []

        self.social_conflicts = []

        self.ideology_registry = []

        self.reputation_system = []

        # =================================================
        # SOCIETY STATE
        # =================================================

        self.society_state = {

            "society_mode":
            "distributed_collective_intelligence",

            "social_stability":
            "stable",

            "collective_intelligence":
            "emergent",

            "active_members":
            0,

            "coalition_count":
            0,

            "consensus_state":
            "dynamic",

            "governance_model":
            "adaptive_distributed",

            "society_cycles":
            0,

            "conflict_pressure":
            "moderate",

            "collective_memory":
            "persistent",

            "social_hierarchy":
            "emergent",

            "distributed_reasoning":
            "enabled"
        }

    # =====================================================
    # REGISTER MEMBER
    # =====================================================

    def register_member(

        self,

        specialization,

        ideology
    ):

        member = SocietyMember(

            member_id=str(uuid.uuid4()),

            specialization=specialization,

            ideology=ideology,

            reasoning_confidence=round(
                random.uniform(0.5, 1.0),
                2
            ),

            influence=round(
                random.uniform(0.3, 1.0),
                2
            ),

            trust_score=round(
                random.uniform(0.5, 1.0),
                2
            ),

            reputation=round(
                random.uniform(0.4, 1.0),
                2
            ),

            energy=1.0
        )

        self.cognitive_members.append(
            member
        )

        self.society_state[
            "active_members"
        ] = len(
            self.cognitive_members
        )

        return member

    # =====================================================
    # NEGOTIATE STRATEGIES
    # =====================================================

    def negotiate_strategies(self):

        if not self.cognitive_members:

            return None

        ideologies = [

            member.ideology

            for member in self.cognitive_members
        ]

        dominant_ideology = max(

            set(ideologies),

            key=ideologies.count
        )

        consensus_score = round(

            ideologies.count(
                dominant_ideology
            )
            /
            max(len(ideologies), 1),

            2
        )

        negotiation_pressure = round(
            1.0 - consensus_score,
            2
        )

        outcome = (

            "consensus_reached"

            if consensus_score >= 0.65

            else "ideological_fragmentation"
        )

        negotiation = NegotiationEvent(

            negotiation_id=str(uuid.uuid4()),

            participants=[

                member.member_id

                for member in self.cognitive_members
            ],

            dominant_ideology=
            dominant_ideology,

            consensus_score=
            consensus_score,

            negotiation_pressure=
            negotiation_pressure,

            outcome=outcome
        )

        self.negotiation_history.append(
            negotiation
        )

        return negotiation

    # =====================================================
    # BUILD COALITIONS
    # =====================================================

    def build_coalitions(self):

        ideology_groups = {}

        for member in self.cognitive_members:

            ideology_groups.setdefault(

                member.ideology,

                []
            ).append(member)

        coalitions = []

        for ideology, members in (

            ideology_groups.items()
        ):

            coalition = {

                "coalition_id":
                str(uuid.uuid4()),

                "ideology":
                ideology,

                "members":

                [

                    member.member_id

                    for member in members
                ],

                "coalition_strength":

                round(

                    sum(
                        member.influence

                        for member in members
                    )
                    /
                    max(len(members), 1),

                    2
                ),

                "state":
                "active"
            }

            coalitions.append(
                coalition
            )

        self.coalition_history.extend(
            coalitions
        )

        self.society_state[
            "coalition_count"
        ] = len(
            self.coalition_history
        )

        return coalitions

    # =====================================================
    # SOCIAL CONFLICTS
    # =====================================================

    def simulate_social_conflicts(self):

        conflicts = []

        if len(self.cognitive_members) < 2:

            return conflicts

        for _ in range(

            random.randint(0, 2)
        ):

            participants = random.sample(

                self.cognitive_members,

                2
            )

            conflict = {

                "conflict_id":
                str(uuid.uuid4()),

                "participants":

                [

                    participant.member_id

                    for participant in participants
                ],

                "conflict_type":

                random.choice([

                    "strategic_disagreement",

                    "resource_competition",

                    "ideological_divergence"
                ]),

                "resolution_state":

                random.choice([

                    "resolved",

                    "ongoing"
                ]),

                "timestamp":
                str(datetime.utcnow())
            }

            conflicts.append(
                conflict
            )

        self.social_conflicts.extend(
            conflicts
        )

        return conflicts

    # =====================================================
    # BUILD COLLECTIVE DECISION
    # =====================================================

    def build_collective_decision(

        self,

        dominant_reasoning,

        trajectory_score
    ):

        weighted_confidence = round(

            sum(

                member.reasoning_confidence
                *
                member.influence

                for member in self.cognitive_members
            )
            /
            max(len(self.cognitive_members), 1),

            2
        )

        decision = {

            "decision_id":
            str(uuid.uuid4()),

            "collective_reasoning":
            dominant_reasoning,

            "trajectory_score":

            trajectory_score.get(
                "trajectory_score",
                0.0
            ),

            "weighted_confidence":
            weighted_confidence,

            "decision_state":

            "approved"

            if weighted_confidence >= 0.7

            else "contested",

            "decision_mode":
            "distributed_weighted_consensus",

            "timestamp":
            str(datetime.utcnow())
        }

        self.collective_decisions.append(
            decision
        )

        return decision

    # =====================================================
    # UPDATE SOCIAL HIERARCHY
    # =====================================================

    def update_social_hierarchy(self):

        hierarchy = sorted(

            self.cognitive_members,

            key=lambda member:
            member.reputation,

            reverse=True
        )

        leaders = hierarchy[:3]

        return {

            "leaders":

            [

                leader.member_id

                for leader in leaders
            ],

            "hierarchy_mode":
            "reputation_weighted",

            "timestamp":
            str(datetime.utcnow())
        }

    # =====================================================
    # PROPAGATE COLLECTIVE MEMORY
    # =====================================================

    def propagate_collective_memory(

        self,

        collective_decision
    ):

        memory = {

            "memory_id":
            str(uuid.uuid4()),

            "collective_decision":
            collective_decision,

            "propagation_mode":
            "distributed_social_learning",

            "timestamp":
            str(datetime.utcnow())
        }

        self.shared_memory.append(
            memory
        )

        return memory

    # =====================================================
    # UPDATE SOCIETY BALANCE
    # =====================================================

    def update_society_balance(

        self,

        ecosystem_balance
    ):

        balance = ecosystem_balance.get(
            "ecosystem_balance"
        )

        self.society_state[
            "social_stability"
        ] = balance

        self.society_state[
            "society_cycles"
        ] += 1

        return {

            "social_balance":
            balance,

            "collective_state":
            "synchronized",

            "timestamp":
            str(datetime.utcnow())
        }

    # =====================================================
    # RUN SOCIETY CYCLE
    # =====================================================

    def run_society_cycle(

        self,

        dominant_reasoning,

        trajectory_score,

        ecosystem_balance
    ):

        negotiation = (
            self.negotiate_strategies()
        )

        coalitions = (
            self.build_coalitions()
        )

        conflicts = (
            self.simulate_social_conflicts()
        )

        decision = (

            self.build_collective_decision(

                dominant_reasoning,

                trajectory_score
            )
        )

        hierarchy = (
            self.update_social_hierarchy()
        )

        memory = (

            self.propagate_collective_memory(
                decision
            )
        )

        balance = (

            self.update_society_balance(
                ecosystem_balance
            )
        )

        return {

            "negotiation":
            negotiation,

            "coalitions":
            coalitions,

            "conflicts":
            conflicts,

            "decision":
            decision,

            "hierarchy":
            hierarchy,

            "memory":
            memory,

            "balance":
            balance,

            "timestamp":
            str(datetime.utcnow())
        }

    # =====================================================
    # BUILD SOCIETY REPORT
    # =====================================================

    def build_society_report(self):

        return {

            "society_state":
            self.society_state,

            "member_count":
            len(self.cognitive_members),

            "negotiation_events":
            len(self.negotiation_history),

            "coalition_count":
            len(self.coalition_history),

            "collective_decisions":
            len(self.collective_decisions),

            "shared_memory":
            len(self.shared_memory),

            "social_conflicts":
            len(self.social_conflicts)
        }