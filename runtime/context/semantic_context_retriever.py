# ============================================
# NEXRYN SEMANTIC CONTEXT RETRIEVER
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# SEMANTIC CONTEXT RETRIEVER
# ============================================

class SemanticContextRetriever:

    # ========================================
    # INITIALIZE RETRIEVER
    # ========================================

    def __init__(self):

        # ====================================
        # RETRIEVAL MEMORY
        # ====================================

        self.retrieval_memory = []

        # ====================================
        # QUERY HISTORY
        # ====================================

        self.query_history = []

        # ====================================
        # RETRIEVAL EVENTS
        # ====================================

        self.retrieval_events = []

        # ====================================
        # SEMANTIC INDEX
        # ====================================

        self.semantic_index = {}

        # ====================================
        # RETRIEVAL CLUSTERS
        # ====================================

        self.retrieval_clusters = {}

        # ====================================
        # REACTIVATED CONTEXTS
        # ====================================

        self.reactivated_contexts = []

        # ====================================
        # EXECUTIVE MATCHES
        # ====================================

        self.executive_matches = []

        # ====================================
        # RECURSIVE MATCHES
        # ====================================

        self.recursive_matches = []

        # ====================================
        # RETRIEVER STATE
        # ====================================

        self.retriever_state = {

            "retrieval_mode":
            "recursive_semantic_retrieval",

            "semantic_matching":
            "enabled",

            "importance_aware":
            "enabled",

            "lazy_reactivation":
            "enabled",

            "recursive_retrieval":
            "enabled",

            "cluster_routing":
            "enabled",

            "executive_awareness":
            "enabled",

            "retrieval_cycles":
            0
        }

    # ========================================
    # REGISTER EVENT
    # ========================================

    def register_event(

        self,

        event_type,

        payload
    ):

        event = {

            "event_id":
            str(uuid.uuid4()),

            "event_type":
            event_type,

            "payload":
            payload,

            "timestamp":
            str(datetime.utcnow())
        }

        self.retrieval_events.append(
            event
        )

        return event

    # ========================================
    # TOKENIZE QUERY
    # ========================================

    def tokenize_query(

        self,

        query
    ):

        tokens = (

            query
            .lower()
            .replace("-", "_")
            .split("_")
        )

        return [

            token.strip()

            for token in tokens

            if token.strip()
        ]

    # ========================================
    # BUILD SEMANTIC INDEX
    # ========================================

    def build_semantic_index(

        self,

        contexts
    ):

        self.semantic_index = {}

        for key in contexts:

            tokens = self.tokenize_query(
                key
            )

            for token in tokens:

                if token not in self.semantic_index:

                    self.semantic_index[
                        token
                    ] = []

                self.semantic_index[
                    token
                ].append(key)

        return self.semantic_index

    # ========================================
    # COMPUTE SEMANTIC SCORE
    # ========================================

    def compute_semantic_score(

        self,

        query_tokens,

        context_key
    ):

        context_tokens = (

            self.tokenize_query(
                context_key
            )
        )

        shared = len(

            set(query_tokens)
            .intersection(

                set(context_tokens)
            )
        )

        total = max(

            len(query_tokens),
            1
        )

        semantic_score = round(

            shared / total,

            4
        )

        return semantic_score

    # ========================================
    # COMPUTE IMPORTANCE SCORE
    # ========================================

    def compute_importance_score(

        self,

        context_key,

        importance_engine=None
    ):

        if importance_engine is None:

            return 0.5

        return (

            importance_engine
            .importance_memory
            .get(
                context_key,
                0.5
            )
        )

    # ========================================
    # COMPUTE EXECUTIVE SCORE
    # ========================================

    def compute_executive_score(

        self,

        context_key
    ):

        executive_tokens = [

            "goal",
            "governance",
            "planning",
            "strategy",
            "mission",
            "executive"
        ]

        score = 0.0

        for token in executive_tokens:

            if token in context_key:

                score += 0.15

        if score > 0:

            self.executive_matches.append(
                context_key
            )

        return round(

            min(score, 1.0),

            4
        )

    # ========================================
    # COMPUTE RECURSIVE SCORE
    # ========================================

    def compute_recursive_score(

        self,

        context_key
    ):

        recursive_tokens = [

            "recursive",
            "meta",
            "cycle",
            "reflection",
            "loop",
            "self"
        ]

        score = 0.0

        for token in recursive_tokens:

            if token in context_key:

                score += 0.20

        if score > 0:

            self.recursive_matches.append(
                context_key
            )

        return round(

            min(score, 1.0),

            4
        )

    # ========================================
    # BUILD RETRIEVAL CLUSTERS
    # ========================================

    def build_retrieval_clusters(

        self,

        context_key
    ):

        cluster = context_key.split("_")[0]

        if cluster not in self.retrieval_clusters:

            self.retrieval_clusters[
                cluster
            ] = []

        self.retrieval_clusters[
            cluster
        ].append(
            context_key
        )

    # ========================================
    # SEARCH CONTEXTS
    # ========================================

    def search_contexts(

        self,

        query,

        contexts,

        importance_engine=None,

        top_k=10
    ):

        query_tokens = (
            self.tokenize_query(
                query
            )
        )

        results = []

        for context_key, context in (

            contexts.items()
        ):

            semantic_score = (

                self.compute_semantic_score(

                    query_tokens,
                    context_key
                )
            )

            importance_score = (

                self.compute_importance_score(

                    context_key,
                    importance_engine
                )
            )

            executive_score = (

                self.compute_executive_score(
                    context_key
                )
            )

            recursive_score = (

                self.compute_recursive_score(
                    context_key
                )
            )

            final_score = (

                semantic_score * 0.50 +

                importance_score * 0.25 +

                executive_score * 0.15 +

                recursive_score * 0.10
            )

            final_score = round(

                min(final_score, 1.0),

                4
            )

            if final_score > 0.10:

                result = {

                    "context_key":
                    context_key,

                    "semantic_score":
                    semantic_score,

                    "importance_score":
                    importance_score,

                    "executive_score":
                    executive_score,

                    "recursive_score":
                    recursive_score,

                    "final_score":
                    final_score,

                    "timestamp":
                    str(datetime.utcnow())
                }

                results.append(
                    result
                )

                self.build_retrieval_clusters(
                    context_key
                )

        results = sorted(

            results,

            key=lambda item:

            item[
                "final_score"
            ],

            reverse=True
        )

        return results[:top_k]

    # ========================================
    # REACTIVATE CONTEXT
    # ========================================

    def reactivate_context(

        self,

        context_key,

        context_bus=None
    ):

        if context_bus is None:

            return None

        if context_key not in (

            context_bus
            .dormant_contexts
        ):

            return None

        context = (

            context_bus
            .dormant_contexts
            .pop(context_key)
        )

        context_bus.active_contexts[
            context_key
        ] = context

        self.reactivated_contexts.append(
            context_key
        )

        report = {

            "reactivated_context":
            context_key,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "context_reactivated",

            report
        )

        return report

    # ========================================
    # RETRIEVE
    # ========================================

    def retrieve(

        self,

        query,

        context_bus,

        importance_engine=None,

        top_k=10
    ):

        # ====================================
        # BUILD CONTEXT POOL
        # ====================================

        contexts = {

            **context_bus.active_contexts,

            **context_bus.dormant_contexts
        }

        # ====================================
        # BUILD INDEX
        # ====================================

        semantic_index = (

            self.build_semantic_index(
                contexts
            )
        )

        # ====================================
        # SEARCH
        # ====================================

        retrieval_results = (

            self.search_contexts(

                query=query,

                contexts=contexts,

                importance_engine=importance_engine,

                top_k=top_k
            )
        )

        # ====================================
        # REACTIVATE BEST MATCH
        # ====================================

        if retrieval_results:

            best_match = retrieval_results[0]

            best_key = best_match[
                "context_key"
            ]

            self.reactivate_context(

                best_key,

                context_bus
            )

        # ====================================
        # QUERY REPORT
        # ====================================

        report = {

            "query":
            query,

            "query_tokens":
            self.tokenize_query(
                query
            ),

            "retrieval_results":
            retrieval_results,

            "result_count":
            len(retrieval_results),

            "semantic_index_size":
            len(semantic_index),

            "timestamp":
            str(datetime.utcnow())
        }

        self.query_history.append(
            report
        )

        self.retrieval_memory.append(
            retrieval_results
        )

        self.retriever_state[
            "retrieval_cycles"
        ] += 1

        self.register_event(

            "retrieval_cycle",

            report
        )

        return report

    # ========================================
    # BUILD RETRIEVAL GRAPH
    # ========================================

    def build_retrieval_graph(self):

        nodes = []

        edges = []

        node_id = 0

        all_contexts = []

        for cluster, members in (

            self.retrieval_clusters.items()
        ):

            for member in members:

                all_contexts.append(
                    member
                )

        unique_contexts = list(
            set(all_contexts)
        )

        node_map = {}

        for context in unique_contexts:

            nodes.append({

                "node_id":
                node_id,

                "context":
                context
            })

            node_map[
                context
            ] = node_id

            node_id += 1

        for source in unique_contexts:

            for target in unique_contexts:

                if source == target:

                    continue

                shared = len(

                    set(
                        source.split("_")
                    ).intersection(

                        set(
                            target.split("_")
                        )
                    )
                )

                if shared > 0:

                    edges.append({

                        "source":
                        node_map[source],

                        "target":
                        node_map[target],

                        "relation":
                        "semantic_retrieval",

                        "weight":
                        shared
                    })

        return {

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "recursive_semantic_retrieval_graph"
        }

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        retrieval_graph = (
            self.build_retrieval_graph()
        )

        return {

            "retriever_state":
            self.retriever_state,

            "retrieval_memory":
            len(self.retrieval_memory),

            "query_history":
            len(self.query_history),

            "retrieval_events":
            len(self.retrieval_events),

            "semantic_index":
            len(self.semantic_index),

            "retrieval_clusters":
            len(self.retrieval_clusters),

            "reactivated_contexts":
            len(self.reactivated_contexts),

            "executive_matches":
            len(self.executive_matches),

            "recursive_matches":
            len(self.recursive_matches),

            "retrieval_graph_nodes":
            len(
                retrieval_graph["nodes"]
            ),

            "retrieval_graph_edges":
            len(
                retrieval_graph["edges"]
            ),

            "latest_query":

            self.query_history[-1]

            if self.query_history

            else {}
        }


# ============================================
# GLOBAL RETRIEVER
# ============================================

semantic_context_retriever = (
    SemanticContextRetriever()
)