# ============================================
# NEXRYN SEMANTIC MEMORY RETRIEVER
# ============================================

from datetime import datetime

import math


# ============================================
# SEMANTIC MEMORY RETRIEVER
# ============================================

class SemanticMemoryRetriever:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # MEMORY INDEX
        # ====================================

        self.memory_index = []

        # ====================================
        # RETRIEVAL HISTORY
        # ====================================

        self.retrieval_history = []

        # ====================================
        # CONFIGURATION
        # ====================================

        self.configuration = {

            "semantic_similarity":
            True,

            "importance_weighting":
            True,

            "adaptive_retrieval":
            True,

            "concept_matching":
            True,

            "cluster_retrieval":
            True
        }

        # ====================================
        # METRICS
        # ====================================

        self.metrics = {

            "indexed_memories":
            0,

            "retrieval_cycles":
            0,

            "retrieved_memories":
            0,

            "semantic_matches":
            0
        }

    # ========================================
    # EXTRACT CONCEPTS
    # ========================================

    def extract_concepts(

        self,

        memory
    ):

        concepts = []

        semantic_abstractions = (

            memory.get(
                "semantic_abstractions",
                []
            )
        )

        for abstraction in (
            semantic_abstractions
        ):

            concept = (

                abstraction.get(
                    "semantic_concept"
                )
            )

            if concept:

                concepts.append(
                    concept
                )

        winner_hypothesis = (

            memory.get(
                "winner_hypothesis",
                {}
            )
        )

        hypothesis_type = (

            winner_hypothesis.get(
                "type"
            )
        )

        if hypothesis_type:

            concepts.append(
                hypothesis_type
            )

        return list(
            set(concepts)
        )

    # ========================================
    # INDEX MEMORY
    # ========================================

    def index_memory(

        self,

        memory
    ):

        indexed_memory = {

            "memory":
            memory,

            "concepts":

            self.extract_concepts(
                memory
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.memory_index.append(
            indexed_memory
        )

        self.metrics[
            "indexed_memories"
        ] += 1

        return indexed_memory

    # ========================================
    # COMPUTE SIMILARITY
    # ========================================

    def compute_similarity(

        self,

        query_concepts,

        memory_concepts
    ):

        if not query_concepts:

            return 0.0

        query_set = set(
            query_concepts
        )

        memory_set = set(
            memory_concepts
        )

        intersection = len(

            query_set.intersection(
                memory_set
            )
        )

        union = len(

            query_set.union(
                memory_set
            )
        )

        if union == 0:

            return 0.0

        similarity = (
            intersection / union
        )

        return round(
            similarity,
            4
        )

    # ========================================
    # RETRIEVE SIMILAR MEMORIES
    # ========================================

    def retrieve_similar_memories(

        self,

        runtime_context,

        top_k=5
    ):

        query_concepts = (

            self.extract_concepts(
                runtime_context
            )
        )

        scored_memories = []

        for indexed_memory in (
            self.memory_index
        ):

            memory_concepts = (

                indexed_memory.get(
                    "concepts",
                    []
                )
            )

            similarity_score = (

                self.compute_similarity(

                    query_concepts,

                    memory_concepts
                )
            )

            if similarity_score > 0:

                scored_memories.append({

                    "memory":

                    indexed_memory.get(
                        "memory",
                        {}
                    ),

                    "concepts":
                    memory_concepts,

                    "similarity":
                    similarity_score
                })

        scored_memories = sorted(

            scored_memories,

            key=lambda x:
            x["similarity"],

            reverse=True
        )

        retrieved = (
            scored_memories[:top_k]
        )

        self.metrics[
            "retrieval_cycles"
        ] += 1

        self.metrics[
            "retrieved_memories"
        ] += len(
            retrieved
        )

        self.metrics[
            "semantic_matches"
        ] += len(
            retrieved
        )

        retrieval_report = {

            "query_concepts":
            query_concepts,

            "retrieved_count":
            len(retrieved),

            "top_similarity":

            retrieved[0][
                "similarity"
            ]

            if retrieved else 0.0,

            "timestamp":
            str(datetime.utcnow())
        }

        self.retrieval_history.append(
            retrieval_report
        )

        return {

            "retrieved_memories":
            retrieved,

            "retrieval_report":
            retrieval_report
        }

    # ========================================
    # BUILD SEMANTIC SUMMARY
    # ========================================

    def build_semantic_summary(self):

        dominant_concepts = {}

        for indexed_memory in (
            self.memory_index
        ):

            concepts = (

                indexed_memory.get(
                    "concepts",
                    []
                )
            )

            for concept in concepts:

                if concept not in (
                    dominant_concepts
                ):

                    dominant_concepts[
                        concept
                    ] = 0

                dominant_concepts[
                    concept
                ] += 1

        ranked_concepts = sorted(

            dominant_concepts.items(),

            key=lambda x:
            x[1],

            reverse=True
        )

        return {

            "dominant_concepts":
            ranked_concepts[:10],

            "indexed_memory_count":

            len(
                self.memory_index
            )
        }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "metrics":
            self.metrics,

            "memory_index_size":

            len(
                self.memory_index
            ),

            "retrieval_history":

            len(
                self.retrieval_history
            ),

            "semantic_summary":

            self.build_semantic_summary()
        }


# ============================================
# GLOBAL RETRIEVER
# ============================================

semantic_memory_retriever = (
    SemanticMemoryRetriever()
)