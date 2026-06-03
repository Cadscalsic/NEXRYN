# ============================================
# NEXRYN RECURSIVE CONTEXT MANAGER
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# CONTEXT MANAGER
# ============================================

class ContextManager:

    # ========================================
    # INITIALIZE CONTEXT MANAGER
    # ========================================

    def __init__(self):

        # ====================================
        # CONTEXT STATE
        # ====================================

        self.context_state = {

            "context_mode":
            "recursive_semantic_runtime",

            "context_compression":
            "adaptive",

            "semantic_routing":
            "enabled",

            "context_lifecycle":
            "hierarchical",

            "reactivation_system":
            "enabled",

            "importance_scoring":
            "enabled",

            "semantic_consolidation":
            "enabled",

            "context_stability":
            "stable",

            "context_cycles":
            0
        }

        # ====================================
        # ACTIVE CONTEXTS
        # ====================================

        self.active_contexts = {}

        # ====================================
        # DORMANT CONTEXTS
        # ====================================

        self.dormant_contexts = {}

        # ====================================
        # ARCHIVED CONTEXTS
        # ====================================

        self.archived_contexts = {}

        # ====================================
        # CONTEXT HISTORY
        # ====================================

        self.context_history = []

        # ====================================
        # COMPRESSION HISTORY
        # ====================================

        self.compression_history = []

        # ====================================
        # CONTEXT IMPORTANCE
        # ====================================

        self.context_importance = {}

        # ====================================
        # CONTEXT ACCESS TRACKING
        # ====================================

        self.context_access = {}

        # ====================================
        # CONTEXT EVENTS
        # ====================================

        self.context_events = []

        # ====================================
        # CONTEXT GRAPH
        # ====================================

        self.context_graph = {

            "nodes": [],
            "edges": []
        }

        # ====================================
        # MEMORY PRESSURE
        # ====================================

        self.memory_pressure = {

            "pressure_score":
            0.0,

            "pressure_state":
            "stable"
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

        self.context_events.append(
            event
        )

        return event

    # ========================================
    # UPDATE ACCESS
    # ========================================

    def update_access(

        self,

        key
    ):

        if key not in self.context_access:

            self.context_access[key] = {

                "usage_count":
                0,

                "last_access":
                str(datetime.utcnow())
            }

        self.context_access[
            key
        ][
            "usage_count"
        ] += 1

        self.context_access[
            key
        ][
            "last_access"
        ] = str(
            datetime.utcnow()
        )

    # ========================================
    # COMPUTE IMPORTANCE SCORE
    # ========================================

    def compute_importance_score(

        self,

        key,

        value
    ):

        usage = (

            self.context_access
            .get(key, {})
            .get("usage_count", 0)
        )

        semantic_score = 0.5

        if any(

            token in key

            for token in [

                "report",
                "trajectory",
                "governance",
                "execution",
                "strategy",
                "evaluation",
                "reasoning"
            ]
        ):

            semantic_score += 0.35

        if isinstance(value, dict):

            semantic_score += min(

                len(value) / 100,

                0.15
            )

        recency_score = 0.25

        usage_score = min(
            usage / 50,
            0.25
        )

        importance = round(

            semantic_score +
            recency_score +
            usage_score,

            4
        )

        self.context_importance[
            key
        ] = importance

        return importance

    # ========================================
    # ANALYZE CONTEXT
    # ========================================

    def analyze_context(

        self,

        runtime_context
    ):

        analysis = {

            "context_size":
            len(runtime_context),

            "high_priority_contexts":
            [],

            "medium_priority_contexts":
            [],

            "low_priority_contexts":
            [],

            "importance_scores":
            {},

            "timestamp":
            str(datetime.utcnow())
        }

        for key, value in runtime_context.items():

            importance = (

                self.compute_importance_score(

                    key,
                    value
                )
            )

            analysis[
                "importance_scores"
            ][key] = importance

            if importance >= 0.85:

                analysis[
                    "high_priority_contexts"
                ].append(key)

            elif importance >= 0.60:

                analysis[
                    "medium_priority_contexts"
                ].append(key)

            else:

                analysis[
                    "low_priority_contexts"
                ].append(key)

        return analysis

    # ========================================
    # SEMANTIC SUMMARIZATION
    # ========================================

    def semantic_summarize_context(

        self,

        value
    ):

        if isinstance(value, dict):

            summarized = {

                "summary_keys":
                list(value.keys())[:10],

                "summary_size":
                len(value),

                "summary_mode":
                "semantic_abstraction"
            }

            return summarized

        if isinstance(value, list):

            return {

                "summary_length":
                len(value),

                "summary_preview":
                value[:3]
            }

        return value

    # ========================================
    # COMPRESS CONTEXT
    # ========================================

    def compress_context(

        self,

        runtime_context,

        analysis
    ):

        compressed_context = {}

        retained_keys = []

        retained = (

            analysis[
                "high_priority_contexts"
            ]

            +

            analysis[
                "medium_priority_contexts"
            ][:10]
        )

        for key in retained:

            value = runtime_context.get(key)

            compressed_context[key] = (

                self.semantic_summarize_context(
                    value
                )
            )

            retained_keys.append(key)

        compression_ratio = round(

            1 -

            (
                len(retained_keys)
                /
                max(
                    len(runtime_context),
                    1
                )
            ),

            4
        )

        compression_report = {

            "original_context_size":
            len(runtime_context),

            "compressed_context_size":
            len(compressed_context),

            "retained_keys":
            retained_keys,

            "compression_ratio":
            compression_ratio,

            "compression_mode":
            "semantic_recursive_compression",

            "timestamp":
            str(datetime.utcnow())
        }

        self.compression_history.append(
            compression_report
        )

        return (

            compressed_context,

            compression_report
        )

    # ========================================
    # ACTIVATE CONTEXTS
    # ========================================

    def activate_contexts(

        self,

        compressed_context
    ):

        activated = []

        self.active_contexts.clear()

        for key, value in compressed_context.items():

            self.active_contexts[key] = {

                "value":
                value,

                "activated_at":
                str(datetime.utcnow()),

                "ttl":
                10,

                "usage_count":
                0
            }

            activated.append(key)

        report = {

            "activated_contexts":
            activated,

            "activation_count":
            len(activated),

            "timestamp":
            str(datetime.utcnow())
        }

        return report

    # ========================================
    # MOVE DORMANT CONTEXTS
    # ========================================

    def move_dormant_contexts(

        self,

        runtime_context,

        compressed_context
    ):

        dormant = []

        for key, value in runtime_context.items():

            if key not in compressed_context:

                self.dormant_contexts[
                    key
                ] = {

                    "value":
                    value,

                    "dormant_since":
                    str(datetime.utcnow()),

                    "reactivation_score":
                    self.context_importance.get(
                        key,
                        0.0
                    )
                }

                dormant.append(key)

        return {

            "dormant_contexts":
            dormant,

            "dormant_count":
            len(dormant),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # REACTIVATE CONTEXT
    # ========================================

    def reactivate_context(

        self,

        key
    ):

        if key not in self.dormant_contexts:

            return None

        context = self.dormant_contexts.pop(
            key
        )

        self.active_contexts[
            key
        ] = context

        self.register_event(

            "context_reactivated",

            {

                "context":
                key
            }
        )

        return context

    # ========================================
    # ARCHIVE CONTEXTS
    # ========================================

    def archive_contexts(self):

        archived = []

        sorted_dormant = sorted(

            self.dormant_contexts.items(),

            key=lambda item:

            item[1].get(
                "reactivation_score",
                0.0
            )
        )

        for key, value in sorted_dormant[:5]:

            self.archived_contexts[
                key
            ] = self.dormant_contexts.pop(
                key
            )

            archived.append(key)

        return {

            "archived_contexts":
            archived,

            "archived_count":
            len(archived),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # BUILD CONTEXT GRAPH
    # ========================================

    def build_context_graph(

        self,

        compressed_context
    ):

        nodes = []
        edges = []

        context_keys = list(
            compressed_context.keys()
        )

        for index, key in enumerate(

            context_keys
        ):

            nodes.append({

                "node_id":
                index,

                "context":
                key,

                "importance":

                self.context_importance.get(
                    key,
                    0.0
                )
            })

        for source in range(

            len(nodes)
        ):

            for target in range(

                source + 1,

                len(nodes)
            ):

                edges.append({

                    "source":
                    source,

                    "target":
                    target,

                    "relation":
                    "semantic_association"
                })

        self.context_graph = {

            "nodes":
            nodes,

            "edges":
            edges
        }

        return {

            "node_count":
            len(nodes),

            "edge_count":
            len(edges),

            "graph_mode":
            "recursive_semantic_graph",

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # ANALYZE MEMORY PRESSURE
    # ========================================

    def analyze_memory_pressure(self):

        total = (

            len(self.active_contexts)

            +

            len(self.dormant_contexts)

            +

            len(self.archived_contexts)
        )

        pressure_score = round(

            min(
                total / 500,
                1.0
            ),

            4
        )

        if pressure_score >= 0.85:

            pressure_state = "critical"

        elif pressure_score >= 0.60:

            pressure_state = "elevated"

        else:

            pressure_state = "stable"

        self.memory_pressure = {

            "pressure_score":
            pressure_score,

            "pressure_state":
            pressure_state
        }

        return self.memory_pressure

    # ========================================
    # CONTEXT CONSOLIDATION
    # ========================================

    def consolidate_contexts(self):

        consolidated = {}

        for key in self.active_contexts:

            prefix = key.split("_")[0]

            if prefix not in consolidated:

                consolidated[prefix] = 0

            consolidated[prefix] += 1

        return {

            "consolidated_groups":
            consolidated,

            "group_count":
            len(consolidated),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN CONTEXT CYCLE
    # ========================================

    def run_context_cycle(

        self,

        runtime_context
    ):

        analysis = (

            self.analyze_context(
                runtime_context
            )
        )

        compressed_context, compression_report = (

            self.compress_context(

                runtime_context,
                analysis
            )
        )

        activation_report = (

            self.activate_contexts(
                compressed_context
            )
        )

        dormant_report = (

            self.move_dormant_contexts(

                runtime_context,
                compressed_context
            )
        )

        archive_report = (
            self.archive_contexts()
        )

        context_graph = (

            self.build_context_graph(
                compressed_context
            )
        )

        memory_pressure = (

            self.analyze_memory_pressure()
        )

        consolidation_report = (

            self.consolidate_contexts()
        )

        self.context_state[
            "context_cycles"
        ] += 1

        context_report = {

            "analysis":
            analysis,

            "compression_report":
            compression_report,

            "activation_report":
            activation_report,

            "dormant_report":
            dormant_report,

            "archive_report":
            archive_report,

            "context_graph":
            context_graph,

            "memory_pressure":
            memory_pressure,

            "consolidation":
            consolidation_report,

            "context_state":
            self.context_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.context_history.append(
            context_report
        )

        self.register_event(

            "context_cycle",

            context_report
        )

        return context_report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "context_state":
            self.context_state,

            "active_contexts":
            len(self.active_contexts),

            "dormant_contexts":
            len(self.dormant_contexts),

            "archived_contexts":
            len(self.archived_contexts),

            "compression_cycles":
            len(self.compression_history),

            "context_history":
            len(self.context_history),

            "context_events":
            len(self.context_events),

            "memory_pressure":
            self.memory_pressure,

            "context_graph_nodes":
            len(
                self.context_graph.get(
                    "nodes",
                    []
                )
            ),

            "context_graph_edges":
            len(
                self.context_graph.get(
                    "edges",
                    []
                )
            ),

            "latest_context":

            self.context_history[-1]

            if self.context_history

            else {}
        }


# ============================================
# GLOBAL CONTEXT MANAGER
# ============================================

context_manager = (
    ContextManager()
)