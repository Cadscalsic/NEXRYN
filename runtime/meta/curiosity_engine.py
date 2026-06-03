# =========================================================
# NEXRYN INTRINSIC CURIOSITY ENGINE
# =========================================================

from datetime import datetime
from dataclasses import dataclass, field

import uuid
import random


# =========================================================
# KNOWLEDGE GAP
# =========================================================

@dataclass
class KnowledgeGap:

    gap_id: str

    concept: str

    uncertainty: float

    novelty_score: float

    exploration_priority: float

    discovered_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# CURIOSITY ENGINE
# =========================================================

class CuriosityEngine:

    # =====================================================
    # INITIALIZE CURIOSITY
    # =====================================================

    def __init__(self):

        self.curiosity_history = []

        self.discovery_graph = []

        self.knowledge_gaps = []

        self.exploration_memory = []

        self.novelty_history = []

        self.intrinsic_rewards = []

        self.unresolved_questions = []

        # =================================================
        # CURIOSITY STATE
        # =================================================

        self.curiosity_state = {

            "curiosity_mode":
            "intrinsic_recursive_exploration",

            "exploration_depth":
            3,

            "question_generation":
            "adaptive",

            "topic_expansion":
            "enabled",

            "discovery_state":
            "recursive",

            "research_cycles":
            0,

            "curiosity_stability":
            "dynamic",

            "novelty_detection":
            "enabled",

            "uncertainty_modeling":
            "active",

            "intrinsic_motivation":
            "enabled",

            "exploration_pressure":
            "adaptive"
        }

    # =====================================================
    # ESTIMATE UNCERTAINTY
    # =====================================================

    def estimate_uncertainty(

        self,

        topic
    ):

        uncertainty = round(

            random.uniform(
                0.3,
                1.0
            ),

            2
        )

        return uncertainty

    # =====================================================
    # COMPUTE NOVELTY
    # =====================================================

    def compute_novelty(

        self,

        topic
    ):

        existing_topics = [

            entry.get(
                "research_topic",
                ""
            )

            for entry in self.curiosity_history
        ]

        if topic not in existing_topics:

            novelty = round(

                random.uniform(
                    0.75,
                    1.0
                ),

                2
            )

        else:

            novelty = round(

                random.uniform(
                    0.2,
                    0.6
                ),

                2
            )

        self.novelty_history.append({

            "topic":
            topic,

            "novelty":
            novelty
        })

        return novelty

    # =====================================================
    # REGISTER KNOWLEDGE GAP
    # =====================================================

    def register_knowledge_gap(

        self,

        topic
    ):

        uncertainty = (
            self.estimate_uncertainty(
                topic
            )
        )

        novelty = (
            self.compute_novelty(
                topic
            )
        )

        gap = KnowledgeGap(

            gap_id=str(uuid.uuid4()),

            concept=topic,

            uncertainty=uncertainty,

            novelty_score=novelty,

            exploration_priority=round(

                (
                    uncertainty
                    +
                    novelty
                ) / 2,

                2
            )
        )

        self.knowledge_gaps.append(
            gap
        )

        return gap

    # =====================================================
    # GENERATE QUESTIONS
    # =====================================================

    def generate_questions(

        self,

        research_topic,

        knowledge_gap
    ):

        questions = []

        uncertainty = (
            knowledge_gap.uncertainty
        )

        novelty = (
            knowledge_gap.novelty_score
        )

        question_count = int(

            (
                uncertainty
                +
                novelty
            ) * 4
        )

        question_templates = [

            "What hidden structures exist?",

            "Can recursive abstraction improve understanding?",

            "What unresolved contradictions remain?",

            "Can adaptive cognition evolve further?",

            "What unknown patterns remain undiscovered?",

            "How can reasoning architectures generalize?",

            "Can symbolic cognition self-optimize?"
        ]

        for _ in range(

            max(question_count, 3)
        ):

            questions.append(

                random.choice(
                    question_templates
                )
            )

        return list(set(questions))

    # =====================================================
    # EXPAND TOPIC
    # =====================================================

    def expand_topic(

        self,

        topic,

        knowledge_gap
    ):

        expansions = []

        novelty = (
            knowledge_gap.novelty_score
        )

        base_topic = str(topic).lower()

        expansions.extend([

            f"recursive_{base_topic}",

            f"adaptive_{base_topic}",

            f"meta_{base_topic}"
        ])

        if novelty >= 0.8:

            expansions.extend([

                f"emergent_{base_topic}",

                f"autonomous_{base_topic}",

                f"self_evolving_{base_topic}"
            ])

        return expansions

    # =====================================================
    # BUILD DISCOVERY GRAPH
    # =====================================================

    def build_discovery_graph(

        self,

        topic,

        questions,

        expansions,

        knowledge_gap
    ):

        graph = {

            "graph_id":
            str(uuid.uuid4()),

            "root_topic":
            topic,

            "uncertainty":
            knowledge_gap.uncertainty,

            "novelty":
            knowledge_gap.novelty_score,

            "question_count":
            len(questions),

            "expansion_count":
            len(expansions),

            "questions":
            questions,

            "expansions":
            expansions,

            "exploration_priority":

            knowledge_gap.exploration_priority,

            "timestamp":
            str(datetime.utcnow())
        }

        self.discovery_graph.append(
            graph
        )

        return graph

    # =====================================================
    # COMPUTE INTRINSIC REWARD
    # =====================================================

    def compute_intrinsic_reward(

        self,

        knowledge_gap,

        discovery_graph
    ):

        reward = round(

            (
                knowledge_gap.novelty_score
                +
                knowledge_gap.uncertainty
            )
            /
            2,

            2
        )

        intrinsic_reward = {

            "reward_id":
            str(uuid.uuid4()),

            "topic":
            knowledge_gap.concept,

            "reward":
            reward,

            "reward_type":
            "intrinsic_exploration",

            "timestamp":
            str(datetime.utcnow())
        }

        self.intrinsic_rewards.append(
            intrinsic_reward
        )

        return intrinsic_reward

    # =====================================================
    # UPDATE EXPLORATION PRESSURE
    # =====================================================

    def update_exploration_pressure(self):

        if len(self.curiosity_history) >= 10:

            self.curiosity_state[
                "exploration_pressure"
            ] = "high"

        elif len(self.curiosity_history) >= 5:

            self.curiosity_state[
                "exploration_pressure"
            ] = "moderate"

        else:

            self.curiosity_state[
                "exploration_pressure"
            ] = "adaptive"

    # =====================================================
    # RUN CURIOSITY CYCLE
    # =====================================================

    def run_curiosity_cycle(

        self,

        research_topic
    ):

        knowledge_gap = (

            self.register_knowledge_gap(
                research_topic
            )
        )

        questions = (

            self.generate_questions(

                research_topic,

                knowledge_gap
            )
        )

        expansions = (

            self.expand_topic(

                research_topic,

                knowledge_gap
            )
        )

        discovery_graph = (

            self.build_discovery_graph(

                topic=research_topic,

                questions=questions,

                expansions=expansions,

                knowledge_gap=knowledge_gap
            )
        )

        intrinsic_reward = (

            self.compute_intrinsic_reward(

                knowledge_gap,

                discovery_graph
            )
        )

        self.update_exploration_pressure()

        curiosity_report = {

            "research_topic":
            research_topic,

            "knowledge_gap":
            knowledge_gap,

            "generated_questions":
            questions,

            "topic_expansions":
            expansions,

            "discovery_graph":
            discovery_graph,

            "intrinsic_reward":
            intrinsic_reward,

            "curiosity_depth":

            len(questions)
            +
            len(expansions),

            "curiosity_state":
            "active_recursive",

            "timestamp":
            str(datetime.utcnow())
        }

        self.curiosity_history.append(
            curiosity_report
        )

        self.curiosity_state[
            "research_cycles"
        ] += 1

        return curiosity_report

    # =====================================================
    # BUILD REPORT
    # =====================================================

    def build_report(self):

        return {

            "curiosity_state":
            self.curiosity_state,

            "history_size":
            len(self.curiosity_history),

            "discovery_graphs":
            len(self.discovery_graph),

            "knowledge_gaps":
            len(self.knowledge_gaps),

            "intrinsic_rewards":
            len(self.intrinsic_rewards),

            "latest_cycle":

            self.curiosity_history[-1]

            if self.curiosity_history

            else {}
        }