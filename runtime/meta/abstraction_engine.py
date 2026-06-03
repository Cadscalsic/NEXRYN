# =========================================================
# NEXRYN ADVANCED ABSTRACTION ENGINE
# =========================================================

from datetime import datetime
from collections import Counter


# =========================================================
# ABSTRACTION ENGINE
# =========================================================

class AbstractionEngine:

    def __init__(self):

        # =================================================
        # ENGINE STATE
        # =================================================

        self.abstraction_state = {

            "abstraction_mode":
            "recursive_symbolic_synthesis",

            "semantic_fusion":
            "enabled",

            "hierarchy_growth":
            "active",

            "concept_compression":
            "adaptive",

            "symbolic_generalization":
            "enabled",

            "graph_abstraction":
            "enabled",

            "cross_task_generalization":
            "enabled",

            "meta_abstraction":
            "enabled",

            "abstraction_cycles":
            0,

            "abstraction_stability":
            "stable"
        }

        # =================================================
        # INTERNAL MEMORY
        # =================================================

        self.abstraction_history = []

        self.abstract_concepts = []

        self.semantic_hierarchy = []

        self.abstraction_memory = []

        self.meta_abstractions = []

    # =====================================================
    # EXTRACT CORE CONCEPTS
    # =====================================================

    def extract_core_concepts(

        self,

        discovery_report
    ):

        concepts = []

        branches = (

            discovery_report.get(

                "branches",

                []
            )
        )

        for branch in branches:

            concept = branch.get(
                "concept"
            )

            if concept:

                concepts.append(
                    str(concept)
                )

        # =================================================
        # FALLBACK EXTRACTION
        # =================================================

        semantic_graph = discovery_report.get(
            "semantic_graph",
            {}
        )

        graph_nodes = semantic_graph.get(
            "concept_nodes",
            []
        )

        for node in graph_nodes:

            concept = node.get(
                "concept"
            )

            if concept:

                concepts.append(
                    str(concept)
                )

        return list(set(concepts))

    # =====================================================
    # GENERATE ABSTRACT CONCEPTS
    # =====================================================

    def generate_abstractions(

        self,

        concepts
    ):

        abstractions = []

        joined_concepts = " ".join(
            concepts
        ).lower()

        # -------------------------------------------------
        # SYMBOLIC TRANSFORMATION
        # -------------------------------------------------

        if (

            "transformation" in joined_concepts

            or

            "remapping" in joined_concepts
        ):

            abstractions.append({

                "abstraction":
                "symbolic_state_transition",

                "abstraction_type":
                "high_level_reasoning",

                "confidence":
                0.95,

                "generalization_score":
                0.90
            })

        # -------------------------------------------------
        # RECURSIVE
        # -------------------------------------------------

        if "recursive" in joined_concepts:

            abstractions.append({

                "abstraction":
                "recursive_cognitive_expansion",

                "abstraction_type":
                "meta_reasoning",

                "confidence":
                0.93,

                "generalization_score":
                0.91
            })

        # -------------------------------------------------
        # ADAPTIVE
        # -------------------------------------------------

        if "adaptive" in joined_concepts:

            abstractions.append({

                "abstraction":
                "adaptive_symbolic_evolution",

                "abstraction_type":
                "evolutionary_reasoning",

                "confidence":
                0.92,

                "generalization_score":
                0.88
            })

        # -------------------------------------------------
        # STRUCTURAL PRESERVATION
        # -------------------------------------------------

        if (

            "preservation" in joined_concepts

            or

            "conservation" in joined_concepts
        ):

            abstractions.append({

                "abstraction":
                "structural_state_preservation",

                "abstraction_type":
                "structural_reasoning",

                "confidence":
                0.90,

                "generalization_score":
                0.86
            })

        # -------------------------------------------------
        # GENERAL FALLBACK
        # -------------------------------------------------

        if not abstractions:

            abstractions.append({

                "abstraction":
                "generalized_cognitive_pattern",

                "abstraction_type":
                "general_reasoning",

                "confidence":
                0.70,

                "generalization_score":
                0.60
            })

        return abstractions

    # =====================================================
    # BUILD SEMANTIC HIERARCHY
    # =====================================================

    def build_semantic_hierarchy(

        self,

        abstractions
    ):

        hierarchy = {

            "hierarchy_depth":
            len(abstractions),

            "hierarchy_nodes":
            abstractions,

            "hierarchy_mode":
            "recursive_semantic",

            "hierarchy_growth":
            "dynamic",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.semantic_hierarchy.append(
            hierarchy
        )

        return hierarchy

    # =====================================================
    # GRAPH ABSTRACTION
    # =====================================================

    def extract_graph_patterns(

        self,

        semantic_graph
    ):

        graph_patterns = []

        nodes = semantic_graph.get(
            "concept_nodes",
            []
        )

        if len(nodes) >= 3:

            graph_patterns.append({

                "pattern":
                "multi_concept_semantic_cluster",

                "complexity":
                "medium",

                "node_count":
                len(nodes)
            })

        if len(nodes) >= 5:

            graph_patterns.append({

                "pattern":
                "hierarchical_semantic_network",

                "complexity":
                "high",

                "node_count":
                len(nodes)
            })

        return graph_patterns

    # =====================================================
    # META ABSTRACTION
    # =====================================================

    def build_meta_abstractions(

        self,

        abstractions
    ):

        meta_abstractions = []

        abstraction_names = [

            abstraction["abstraction"]

            for abstraction in abstractions
        ]

        joined = " ".join(
            abstraction_names
        ).lower()

        if (

            "symbolic" in joined

            and

            "adaptive" in joined
        ):

            meta_abstractions.append({

                "meta_abstraction":
                "dynamic_symbolic_transformation",

                "meta_type":
                "cross_reasoning_fusion",

                "confidence":
                0.96
            })

        if (

            "recursive" in joined

            and

            "structural" in joined
        ):

            meta_abstractions.append({

                "meta_abstraction":
                "recursive_structural_reasoning",

                "meta_type":
                "hierarchical_cognition",

                "confidence":
                0.94
            })

        self.meta_abstractions.extend(
            meta_abstractions
        )

        return meta_abstractions

    # =====================================================
    # COMPRESS KNOWLEDGE
    # =====================================================

    def compress_knowledge(

        self,

        abstractions
    ):

        compressed = {

            "compression_mode":
            "symbolic_semantic",

            "compressed_concepts":

            [

                abstraction["abstraction"]

                for abstraction in abstractions
            ],

            "compression_ratio":

            round(

                len(abstractions)
                /
                max(len(abstractions) * 2, 1),

                2
            ),

            "compression_efficiency":

            round(

                1.0
                -
                (
                    1
                    /
                    max(len(abstractions), 1)
                ),

                2
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return compressed

    # =====================================================
    # STORE ABSTRACTIONS
    # =====================================================

    def store_abstractions(

        self,

        abstractions
    ):

        for abstraction in abstractions:

            self.abstraction_memory.append({

                "abstraction":
                abstraction,

                "timestamp":
                str(
                    datetime.utcnow()
                ),

                "reuse_count":
                0
            })

    # =====================================================
    # CROSS TASK GENERALIZATION
    # =====================================================

    def generalize_across_tasks(self):

        abstraction_counter = Counter()

        for memory in self.abstraction_memory:

            abstraction_name = (

                memory["abstraction"].get(
                    "abstraction",
                    "unknown"
                )
            )

            abstraction_counter[
                abstraction_name
            ] += 1

        generalized_patterns = []

        for abstraction, frequency in (

            abstraction_counter.items()
        ):

            if frequency >= 2:

                generalized_patterns.append({

                    "generalized_pattern":
                    abstraction,

                    "reuse_frequency":
                    frequency,

                    "generalization_strength":
                    round(
                        min(
                            frequency / 10,
                            1.0
                        ),
                        2
                    )
                })

        return generalized_patterns

    # =====================================================
    # RUN ABSTRACTION CYCLE
    # =====================================================

    def run_abstraction_cycle(

        self,

        discovery_report
    ):

        concepts = (

            self.extract_core_concepts(

                discovery_report
            )
        )

        abstractions = (

            self.generate_abstractions(

                concepts
            )
        )

        hierarchy = (

            self.build_semantic_hierarchy(

                abstractions
            )
        )

        semantic_graph = discovery_report.get(
            "semantic_graph",
            {}
        )

        graph_patterns = (

            self.extract_graph_patterns(

                semantic_graph
            )
        )

        meta_abstractions = (

            self.build_meta_abstractions(

                abstractions
            )
        )

        compressed_knowledge = (

            self.compress_knowledge(

                abstractions
            )
        )

        self.store_abstractions(
            abstractions
        )

        generalized_patterns = (

            self.generalize_across_tasks()
        )

        abstraction_report = {

            "core_concepts":
            concepts,

            "abstract_concepts":
            abstractions,

            "semantic_hierarchy":
            hierarchy,

            "graph_patterns":
            graph_patterns,

            "meta_abstractions":
            meta_abstractions,

            "compressed_knowledge":
            compressed_knowledge,

            "generalized_patterns":
            generalized_patterns,

            "abstraction_depth":
            len(abstractions),

            "symbolic_synthesis":
            "active",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.abstraction_history.append(
            abstraction_report
        )

        self.abstract_concepts.extend(
            abstractions
        )

        self.abstraction_state[
            "abstraction_cycles"
        ] += 1

        return abstraction_report

    # =====================================================
    # BUILD REPORT
    # =====================================================

    def build_report(self):

        return {

            "abstraction_state":
            self.abstraction_state,

            "history_size":
            len(
                self.abstraction_history
            ),

            "abstract_concept_count":
            len(
                self.abstract_concepts
            ),

            "semantic_hierarchies":
            len(
                self.semantic_hierarchy
            ),

            "meta_abstraction_count":
            len(
                self.meta_abstractions
            ),

            "abstraction_memory_size":
            len(
                self.abstraction_memory
            ),

            "latest_abstraction":

            self.abstraction_history[-1]

            if self.abstraction_history

            else {}
        }