# ============================================
# NEXRYN MEMORY INDEXING ENGINE
# ============================================

import math
import copy

from datetime import datetime


# ============================================
# MEMORY INDEXING ENGINE
# ============================================

class MemoryIndexingEngine:

    def __init__(self):

        # ========================================
        # MEMORY INDEX
        # ========================================

        self.memory_index = {}

        # ========================================
        # SEMANTIC CLUSTERS
        # ========================================

        self.semantic_clusters = {}

        # ========================================
        # MEMORY GRAPH
        # ========================================

        self.memory_graph = {

            "nodes": [],
            "edges": []
        }

        # ========================================
        # RETRIEVAL HISTORY
        # ========================================

        self.retrieval_history = []

        # ========================================
        # ACTIVATION HISTORY
        # ========================================

        self.activation_history = []

        # ========================================
        # INDEX STATE
        # ========================================

        self.index_state = {

            "index_mode":
            "semantic_recursive_indexing",

            "semantic_retrieval":
            "enabled",

            "associative_activation":
            "enabled",

            "memory_routing":
            "enabled",

            "graph_memory":
            "enabled",

            "adaptive_ranking":
            "enabled",

            "index_stability":
            "stable",

            "index_cycles":
            0
        }

    # ============================================
    # EXTRACT MEMORY TOKENS
    # ============================================

    def extract_tokens(

        self,

        memory_key
    ):

        tokens = memory_key.replace(

            "_",
            " "

        ).lower().split()

        return tokens

    # ============================================
    # BUILD MEMORY VECTOR
    # ============================================

    def build_memory_vector(

        self,

        memory_key
    ):

        tokens = self.extract_tokens(
            memory_key
        )

        vector = {}

        for token in tokens:

            vector[token] = (

                vector.get(
                    token,
                    0
                ) + 1
            )

        return vector

    # ============================================
    # CALCULATE SIMILARITY
    # ============================================

    def calculate_similarity(

        self,

        vector_a,

        vector_b
    ):

        common_tokens = set(

            vector_a.keys()

        ).intersection(

            set(
                vector_b.keys()
            )
        )

        numerator = 0

        for token in common_tokens:

            numerator += (

                vector_a[token]
                * vector_b[token]
            )

        magnitude_a = math.sqrt(

            sum(

                value * value

                for value in vector_a.values()
            )
        )

        magnitude_b = math.sqrt(

            sum(

                value * value

                for value in vector_b.values()
            )
        )

        denominator = (
            magnitude_a * magnitude_b
        )

        if denominator == 0:

            return 0.0

        similarity = numerator / denominator

        return round(
            similarity,
            4
        )

    # ============================================
    # INDEX MEMORY
    # ============================================

    def index_memory(

        self,

        memory_key,

        memory_value
    ):

        memory_vector = (

            self.build_memory_vector(
                memory_key
            )
        )

        indexed_memory = {

            "memory_key":
            memory_key,

            "memory_vector":
            memory_vector,

            "memory_value":
            copy.deepcopy(
                memory_value
            ),

            "semantic_weight":

            len(
                memory_vector
            ),

            "indexed_at":
            str(
                datetime.utcnow()
            )
        }

        self.memory_index[
            memory_key
        ] = indexed_memory

        return indexed_memory

    # ============================================
    # BUILD SEMANTIC CLUSTERS
    # ============================================

    def build_semantic_clusters(self):

        self.semantic_clusters = {}

        memory_keys = list(
            self.memory_index.keys()
        )

        for key_a in memory_keys:

            vector_a = (

                self.memory_index[key_a][
                    "memory_vector"
                ]
            )

            cluster = []

            for key_b in memory_keys:

                if key_a == key_b:

                    continue

                vector_b = (

                    self.memory_index[key_b][
                        "memory_vector"
                    ]
                )

                similarity = (

                    self.calculate_similarity(

                        vector_a,
                        vector_b
                    )
                )

                if similarity >= 0.5:

                    cluster.append({

                        "memory":
                        key_b,

                        "similarity":
                        similarity
                    })

            self.semantic_clusters[
                key_a
            ] = cluster

        return self.semantic_clusters

    # ============================================
    # RETRIEVE RELATED MEMORIES
    # ============================================

    def retrieve_related_memories(

        self,

        query
    ):

        query_vector = (

            self.build_memory_vector(
                query
            )
        )

        retrieved = []

        for memory_key, memory_data in (

            self.memory_index.items()
        ):

            similarity = (

                self.calculate_similarity(

                    query_vector,

                    memory_data[
                        "memory_vector"
                    ]
                )
            )

            if similarity > 0:

                retrieved.append({

                    "memory_key":
                    memory_key,

                    "similarity":
                    similarity,

                    "memory":
                    memory_data
                })

        retrieved = sorted(

            retrieved,

            key=lambda item:
            item["similarity"],

            reverse=True
        )

        retrieval_report = {

            "query":
            query,

            "retrieved_count":

            len(
                retrieved
            ),

            "results":
            retrieved[:10],

            "retrieval_mode":
            "semantic_associative_recall",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.retrieval_history.append(
            retrieval_report
        )

        return retrieval_report

    # ============================================
    # BUILD MEMORY GRAPH
    # ============================================

    def build_memory_graph(self):

        nodes = []
        edges = []

        memory_keys = list(
            self.memory_index.keys()
        )

        for index, key in enumerate(
            memory_keys
        ):

            nodes.append({

                "node_id":
                index,

                "memory":
                key,

                "state":
                "indexed"
            })

        for index in range(

            len(memory_keys) - 1
        ):

            edges.append({

                "source":
                index,

                "target":
                index + 1,

                "relation":
                "semantic_transition"
            })

        self.memory_graph = {

            "node_count":
            len(nodes),

            "edge_count":
            len(edges),

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "semantic_memory_graph",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        return self.memory_graph

    # ============================================
    # ACTIVATE MEMORY
    # ============================================

    def activate_memory(

        self,

        memory_key
    ):

        if memory_key not in self.memory_index:

            return {

                "success":
                False,

                "error":
                "memory_not_found"
            }

        memory = self.memory_index[
            memory_key
        ]

        activation = {

            "memory_key":
            memory_key,

            "semantic_weight":
            memory.get(
                "semantic_weight",
                0
            ),

            "activation_mode":
            "associative_semantic_activation",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.activation_history.append(
            activation
        )

        return {

            "success":
            True,

            "activation":
            activation
        }

    # ============================================
    # RUN INDEXING CYCLE
    # ============================================

    def run_indexing_cycle(

        self,

        runtime_context
    ):

        # ========================================
        # INDEX CONTEXTS
        # ========================================

        indexed_memories = []

        for key, value in (

            runtime_context.items()
        ):

            indexed = self.index_memory(

                key,
                value
            )

            indexed_memories.append(
                indexed
            )

        # ========================================
        # BUILD CLUSTERS
        # ========================================

        semantic_clusters = (

            self.build_semantic_clusters()
        )

        # ========================================
        # BUILD GRAPH
        # ========================================

        memory_graph = (

            self.build_memory_graph()
        )

        # ========================================
        # RETRIEVE IMPORTANT MEMORIES
        # ========================================

        retrieval_report = (

            self.retrieve_related_memories(

                "executive memory reasoning"
            )
        )

        # ========================================
        # BUILD REPORT
        # ========================================

        report = {

            "indexed_memories":

            len(
                indexed_memories
            ),

            "semantic_clusters":

            len(
                semantic_clusters
            ),

            "memory_graph":
            memory_graph,

            "retrieval_report":
            retrieval_report,

            "index_state":
            self.index_state,

            "index_mode":
            "recursive_semantic_indexing",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.index_state[
            "index_cycles"
        ] += 1

        return report

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {

            "index_state":
            self.index_state,

            "indexed_memories":

            len(
                self.memory_index
            ),

            "semantic_clusters":

            len(
                self.semantic_clusters
            ),

            "retrieval_history":

            len(
                self.retrieval_history
            ),

            "activation_history":

            len(
                self.activation_history
            ),

            "memory_graph":
            self.memory_graph
        }


# ============================================
# GLOBAL INDEX ENGINE
# ============================================

memory_indexing_engine = (
    MemoryIndexingEngine()
)