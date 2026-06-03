# ============================================
# NEXRYN CONTEXT IMPORTANCE ENGINE
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# CONTEXT IMPORTANCE ENGINE
# ============================================

class ContextImportanceEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # IMPORTANCE MEMORY
        # ====================================

        self.importance_memory = {}

        # ====================================
        # IMPORTANCE HISTORY
        # ====================================

        self.importance_history = []

        # ====================================
        # SEMANTIC CLUSTERS
        # ====================================

        self.semantic_clusters = {}

        # ====================================
        # ACCESS PATTERNS
        # ====================================

        self.access_patterns = {}

        # ====================================
        # EXECUTIVE CONTEXTS
        # ====================================

        self.executive_contexts = []

        # ====================================
        # RECURSIVE CONTEXTS
        # ====================================

        self.recursive_contexts = []

        # ====================================
        # STABILITY CONTEXTS
        # ====================================

        self.stability_contexts = []

        # ====================================
        # EVENTS
        # ====================================

        self.events = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "importance_mode":
            "recursive_semantic_importance",

            "dynamic_scoring":
            "enabled",

            "semantic_analysis":
            "enabled",

            "recursive_awareness":
            "enabled",

            "executive_awareness":
            "enabled",

            "adaptive_prioritization":
            "enabled",

            "importance_cycles":
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

        self.events.append(
            event
        )

        return event

    # ========================================
    # UPDATE ACCESS PATTERN
    # ========================================

    def update_access_pattern(

        self,

        context_key
    ):

        if context_key not in self.access_patterns:

            self.access_patterns[
                context_key
            ] = {

                "access_count":
                0,

                "last_access":
                str(datetime.utcnow())
            }

        self.access_patterns[
            context_key
        ][
            "access_count"
        ] += 1

        self.access_patterns[
            context_key
        ][
            "last_access"
        ] = str(
            datetime.utcnow()
        )

    # ========================================
    # COMPUTE RECENCY SCORE
    # ========================================

    def compute_recency_score(

        self,

        context
    ):

        timestamp = context.get(
            "timestamp"
        )

        if not timestamp:

            return 0.5

        return 0.75

    # ========================================
    # COMPUTE ACCESS SCORE
    # ========================================

    def compute_access_score(

        self,

        context_key
    ):

        access_data = (

            self.access_patterns.get(
                context_key,
                {}
            )
        )

        access_count = access_data.get(
            "access_count",
            0
        )

        score = min(

            access_count / 50,

            1.0
        )

        return round(
            score,
            4
        )

    # ========================================
    # COMPUTE SEMANTIC SCORE
    # ========================================

    def compute_semantic_score(

        self,

        context_key,

        context
    ):

        score = 0.0

        semantic_tokens = [

            "reasoning",
            "strategy",
            "evaluation",
            "execution",
            "trajectory",
            "governance",
            "recursive",
            "world_model",
            "attention",
            "planning",
            "abstraction",
            "meta",
            "stabilization"
        ]

        for token in semantic_tokens:

            if token in context_key:

                score += 0.08

        if isinstance(context, dict):

            score += min(

                len(context) / 100,

                0.25
            )

        return round(

            min(score, 1.0),

            4
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
            "strategy",
            "mission",
            "planning",
            "executive"
        ]

        score = 0.0

        for token in executive_tokens:

            if token in context_key:

                score += 0.15

        if score > 0:

            self.executive_contexts.append(
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
            "self",
            "reflection",
            "loop",
            "cycle"
        ]

        score = 0.0

        for token in recursive_tokens:

            if token in context_key:

                score += 0.18

        if score > 0:

            self.recursive_contexts.append(
                context_key
            )

        return round(

            min(score, 1.0),

            4
        )

    # ========================================
    # COMPUTE STABILITY SCORE
    # ========================================

    def compute_stability_score(

        self,

        context_key
    ):

        stability_tokens = [

            "stability",
            "compression",
            "governor",
            "recovery",
            "health",
            "pressure"
        ]

        score = 0.0

        for token in stability_tokens:

            if token in context_key:

                score += 0.15

        if score > 0:

            self.stability_contexts.append(
                context_key
            )

        return round(

            min(score, 1.0),

            4
        )

    # ========================================
    # BUILD SEMANTIC CLUSTERS
    # ========================================

    def build_semantic_clusters(

        self,

        context_key
    ):

        cluster = context_key.split("_")[0]

        if cluster not in self.semantic_clusters:

            self.semantic_clusters[
                cluster
            ] = []

        self.semantic_clusters[
            cluster
        ].append(
            context_key
        )

    # ========================================
    # COMPUTE IMPORTANCE
    # ========================================

    def compute_importance(

        self,

        context_key,

        context
    ):

        # ====================================
        # UPDATE ACCESS
        # ====================================

        self.update_access_pattern(
            context_key
        )

        # ====================================
        # SCORES
        # ====================================

        recency_score = (

            self.compute_recency_score(
                context
            )
        )

        access_score = (

            self.compute_access_score(
                context_key
            )
        )

        semantic_score = (

            self.compute_semantic_score(

                context_key,
                context
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

        stability_score = (

            self.compute_stability_score(
                context_key
            )
        )

        # ====================================
        # FINAL SCORE
        # ====================================

        importance_score = (

            recency_score * 0.15 +

            access_score * 0.15 +

            semantic_score * 0.25 +

            executive_score * 0.20 +

            recursive_score * 0.15 +

            stability_score * 0.10
        )

        importance_score = round(

            min(
                importance_score,
                1.0
            ),

            4
        )

        # ====================================
        # STORE MEMORY
        # ====================================

        self.importance_memory[
            context_key
        ] = importance_score

        self.build_semantic_clusters(
            context_key
        )

        report = {

            "context":
            context_key,

            "importance_score":
            importance_score,

            "recency_score":
            recency_score,

            "access_score":
            access_score,

            "semantic_score":
            semantic_score,

            "executive_score":
            executive_score,

            "recursive_score":
            recursive_score,

            "stability_score":
            stability_score,

            "timestamp":
            str(datetime.utcnow())
        }

        self.importance_history.append(
            report
        )

        self.register_event(

            "importance_computed",

            report
        )

        return report

    # ========================================
    # RANK CONTEXTS
    # ========================================

    def rank_contexts(

        self,

        contexts
    ):

        ranked = []

        for key, value in contexts.items():

            report = (

                self.compute_importance(

                    key,
                    value
                )
            )

            ranked.append(report)

        ranked = sorted(

            ranked,

            key=lambda item:

            item[
                "importance_score"
            ],

            reverse=True
        )

        return ranked

    # ========================================
    # FILTER CRITICAL CONTEXTS
    # ========================================

    def filter_critical_contexts(

        self,

        ranked_contexts,

        threshold=0.70
    ):

        critical = []

        for context in ranked_contexts:

            if context.get(

                "importance_score",
                0.0

            ) >= threshold:

                critical.append(
                    context
                )

        return critical

    # ========================================
    # BUILD IMPORTANCE GRAPH
    # ========================================

    def build_importance_graph(self):

        nodes = []

        edges = []

        node_id = 0

        for key, score in (

            self.importance_memory.items()
        ):

            nodes.append({

                "node_id":
                node_id,

                "context":
                key,

                "importance":
                score
            })

            node_id += 1

        for source in range(

            len(nodes)
        ):

            for target in range(

                source + 1,

                len(nodes)
            ):

                source_key = nodes[source][
                    "context"
                ]

                target_key = nodes[target][
                    "context"
                ]

                shared = len(

                    set(
                        source_key.split("_")
                    ).intersection(

                        set(
                            target_key.split("_")
                        )
                    )
                )

                if shared > 0:

                    edges.append({

                        "source":
                        source,

                        "target":
                        target,

                        "relation":
                        "semantic_importance",

                        "weight":
                        shared
                    })

        return {

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "recursive_importance_graph"
        }

    # ========================================
    # RUN IMPORTANCE CYCLE
    # ========================================

    def run_importance_cycle(

        self,

        contexts
    ):

        ranked_contexts = (

            self.rank_contexts(
                contexts
            )
        )

        critical_contexts = (

            self.filter_critical_contexts(
                ranked_contexts
            )
        )

        importance_graph = (

            self.build_importance_graph()
        )

        self.engine_state[
            "importance_cycles"
        ] += 1

        report = {

            "ranked_contexts":
            ranked_contexts,

            "critical_contexts":
            critical_contexts,

            "importance_graph":
            importance_graph,

            "semantic_clusters":
            self.semantic_clusters,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.register_event(

            "importance_cycle",

            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "engine_state":
            self.engine_state,

            "importance_memory":
            len(self.importance_memory),

            "importance_history":
            len(self.importance_history),

            "semantic_clusters":
            len(self.semantic_clusters),

            "executive_contexts":
            len(self.executive_contexts),

            "recursive_contexts":
            len(self.recursive_contexts),

            "stability_contexts":
            len(self.stability_contexts),

            "events":
            len(self.events),

            "latest_importance":

            self.importance_history[-1]

            if self.importance_history

            else {}
        }


# ============================================
# GLOBAL IMPORTANCE ENGINE
# ============================================

context_importance_engine = (
    ContextImportanceEngine()
)