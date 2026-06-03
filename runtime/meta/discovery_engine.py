# =========================================================
# NEXRYN AUTONOMOUS DISCOVERY ENGINE
# =========================================================

from datetime import datetime
from dataclasses import dataclass, field

import uuid
import random
import itertools


# =========================================================
# DISCOVERY NODE
# =========================================================

@dataclass
class DiscoveryNode:

    node_id: str

    concept: str

    novelty_score: float

    abstraction_level: float

    discovery_value: float

    node_type: str

    created_at: str = field(

        default_factory=lambda:
        str(datetime.utcnow())
    )


# =========================================================
# DISCOVERY ENGINE
# =========================================================

class DiscoveryEngine:

    # =====================================================
    # INITIALIZE DISCOVERY
    # =====================================================

    def __init__(self):

        self.discovery_history = []

        self.discovery_branches = []

        self.concept_graph = []

        self.emergent_concepts = []

        self.discovery_memory = []

        self.discovery_scores = []

        self.recursive_expansions = []

        # =================================================
        # DISCOVERY STATE
        # =================================================

        self.discovery_state = {

            "discovery_mode":
            "recursive_autonomous_discovery",

            "abstraction_growth":
            "active",

            "knowledge_expansion":
            "enabled",

            "concept_linking":
            "semantic_adaptive",

            "branching_depth":
            3,

            "discovery_cycles":
            0,

            "discovery_stability":
            "dynamic",

            "emergent_concepts":
            "enabled",

            "recursive_expansion":
            "active",

            "discovery_topology":
            "self_restructuring"
        }

    # =====================================================
    # GENERATE DISCOVERY BRANCHES
    # =====================================================

    def generate_branches(

        self,

        curiosity_report
    ):

        branches = []

        topic_expansions = (

            curiosity_report.get(
                "topic_expansions",
                []
            )
        )

        generated_questions = (

            curiosity_report.get(
                "generated_questions",
                []
            )
        )

        for expansion in topic_expansions:

            branch = DiscoveryNode(

                node_id=str(uuid.uuid4()),

                concept=expansion,

                novelty_score=round(
                    random.uniform(0.5, 1.0),
                    2
                ),

                abstraction_level=round(
                    random.uniform(0.4, 1.0),
                    2
                ),

                discovery_value=round(
                    random.uniform(0.5, 1.0),
                    2
                ),

                node_type="topic_expansion"
            )

            branches.append(branch)

        for question in generated_questions:

            branch = DiscoveryNode(

                node_id=str(uuid.uuid4()),

                concept=question,

                novelty_score=round(
                    random.uniform(0.4, 1.0),
                    2
                ),

                abstraction_level=round(
                    random.uniform(0.3, 1.0),
                    2
                ),

                discovery_value=round(
                    random.uniform(0.5, 1.0),
                    2
                ),

                node_type="question_exploration"
            )

            branches.append(branch)

        return branches

    # =====================================================
    # GENERATE EMERGENT CONCEPTS
    # =====================================================

    def generate_emergent_concepts(

        self,

        branches
    ):

        emergent = []

        concepts = [

            branch.concept

            for branch in branches
        ]

        combinations = list(

            itertools.combinations(
                concepts,
                2
            )
        )

        random.shuffle(combinations)

        for combo in combinations[:3]:

            fused = (

                f"{combo[0]} + {combo[1]}"
            )

            emergent_concept = {

                "concept_id":
                str(uuid.uuid4()),

                "emergent_concept":
                fused,

                "formation_mode":
                "conceptual_fusion",

                "novelty":
                round(
                    random.uniform(0.7, 1.0),
                    2
                ),

                "timestamp":
                str(datetime.utcnow())
            }

            emergent.append(
                emergent_concept
            )

        self.emergent_concepts.extend(
            emergent
        )

        return emergent

    # =====================================================
    # BUILD CONCEPT GRAPH
    # =====================================================

    def build_concept_graph(

        self,

        branches,

        emergent_concepts
    ):

        graph = {

            "graph_id":
            str(uuid.uuid4()),

            "node_count":
            len(branches),

            "nodes":
            [],

            "edges":
            [],

            "topology":
            "semantic_dynamic",

            "timestamp":
            str(datetime.utcnow())
        }

        # -------------------------------------------------
        # CREATE NODES
        # -------------------------------------------------

        for branch in branches:

            node = {

                "node_id":
                branch.node_id,

                "concept":
                branch.concept,

                "novelty":
                branch.novelty_score,

                "abstraction":
                branch.abstraction_level,

                "value":
                branch.discovery_value,

                "node_type":
                branch.node_type
            }

            graph["nodes"].append(node)

        # -------------------------------------------------
        # SEMANTIC EDGES
        # -------------------------------------------------

        for source in graph["nodes"]:

            for target in graph["nodes"]:

                if (

                    source["node_id"]
                    !=
                    target["node_id"]
                ):

                    similarity = round(

                        random.uniform(
                            0.2,
                            1.0
                        ),

                        2
                    )

                    if similarity >= 0.65:

                        edge = {

                            "source":
                            source["node_id"],

                            "target":
                            target["node_id"],

                            "relation":
                            "semantic_association",

                            "strength":
                            similarity
                        }

                        graph["edges"].append(
                            edge
                        )

        # -------------------------------------------------
        # EMERGENT LINKS
        # -------------------------------------------------

        for concept in emergent_concepts:

            graph["nodes"].append({

                "node_id":
                concept["concept_id"],

                "concept":
                concept["emergent_concept"],

                "node_type":
                "emergent_concept"
            })

        self.concept_graph.append(
            graph
        )

        return graph

    # =====================================================
    # SCORE DISCOVERIES
    # =====================================================

    def score_discoveries(

        self,

        branches,

        emergent_concepts
    ):

        scores = []

        for branch in branches:

            score = round(

                (
                    branch.novelty_score
                    +
                    branch.discovery_value
                    +
                    branch.abstraction_level
                )
                /
                3,

                2
            )

            scores.append({

                "concept":
                branch.concept,

                "discovery_score":
                score
            })

        for concept in emergent_concepts:

            scores.append({

                "concept":
                concept["emergent_concept"],

                "discovery_score":
                concept["novelty"]
            })

        self.discovery_scores.extend(
            scores
        )

        return scores

    # =====================================================
    # RECURSIVE EXPANSION
    # =====================================================

    def recursive_discovery_expansion(

        self,

        emergent_concepts
    ):

        recursive_nodes = []

        for concept in emergent_concepts:

            recursive_node = {

                "recursive_id":
                str(uuid.uuid4()),

                "source":
                concept["emergent_concept"],

                "recursive_expansion":

                f"meta_{concept['emergent_concept']}",

                "expansion_depth":
                random.randint(1, 5),

                "timestamp":
                str(datetime.utcnow())
            }

            recursive_nodes.append(
                recursive_node
            )

        self.recursive_expansions.extend(
            recursive_nodes
        )

        return recursive_nodes

    # =====================================================
    # EVALUATE DISCOVERY DEPTH
    # =====================================================

    def evaluate_discovery_depth(

        self,

        branches,

        emergent_concepts
    ):

        total = (

            len(branches)
            +
            len(emergent_concepts)
        )

        if total >= 12:

            return "advanced_recursive"

        elif total >= 6:

            return "moderate_recursive"

        return "basic"

    # =====================================================
    # RUN DISCOVERY CYCLE
    # =====================================================

    def run_discovery_cycle(

        self,

        curiosity_report
    ):

        branches = (

            self.generate_branches(
                curiosity_report
            )
        )

        emergent_concepts = (

            self.generate_emergent_concepts(
                branches
            )
        )

        concept_graph = (

            self.build_concept_graph(

                branches,

                emergent_concepts
            )
        )

        discovery_scores = (

            self.score_discoveries(

                branches,

                emergent_concepts
            )
        )

        recursive_expansion = (

            self.recursive_discovery_expansion(

                emergent_concepts
            )
        )

        discovery_depth = (

            self.evaluate_discovery_depth(

                branches,

                emergent_concepts
            )
        )

        discovery_report = {

            "branch_count":
            len(branches),

            "branches":
            branches,

            "emergent_concepts":
            emergent_concepts,

            "concept_graph":
            concept_graph,

            "discovery_scores":
            discovery_scores,

            "recursive_expansion":
            recursive_expansion,

            "discovery_depth":
            discovery_depth,

            "abstraction_growth":
            "active_recursive",

            "recursive_exploration":
            True,

            "timestamp":
            str(datetime.utcnow())
        }

        self.discovery_history.append(
            discovery_report
        )

        self.discovery_branches.extend(
            branches
        )

        self.discovery_memory.append(
            discovery_report
        )

        self.discovery_state[
            "discovery_cycles"
        ] += 1

        return discovery_report

    # =====================================================
    # BUILD REPORT
    # =====================================================

    def build_report(self):

        return {

            "discovery_state":
            self.discovery_state,

            "history_size":
            len(self.discovery_history),

            "branch_count":
            len(self.discovery_branches),

            "concept_graphs":
            len(self.concept_graph),

            "emergent_concepts":
            len(self.emergent_concepts),

            "recursive_expansions":
            len(self.recursive_expansions),

            "latest_discovery":

            self.discovery_history[-1]

            if self.discovery_history

            else {}
        }