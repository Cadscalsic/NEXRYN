# ============================================
# NEXRYN RECURSIVE CONTEXT BUS
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# CONTEXT BUS
# ============================================

class ContextBus:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # CONTEXT REGISTRIES
        # ====================================

        self.active_contexts = {}

        self.dormant_contexts = {}

        self.archived_contexts = {}

        # ====================================
        # CONTEXT PRIORITIES
        # ====================================

        self.context_priorities = {}

        # ====================================
        # CONTEXT IMPORTANCE
        # ====================================

        self.context_importance = {}

        # ====================================
        # CONTEXT ACCESS
        # ====================================

        self.context_access = {}

        # ====================================
        # CONTEXT HISTORY
        # ====================================

        self.context_history = []

        # ====================================
        # CONTEXT EVENTS
        # ====================================

        self.context_events = []

        # ====================================
        # CONTEXT CONSOLIDATION
        # ====================================

        self.consolidated_contexts = {}

        # ====================================
        # HEALTH STATE
        # ====================================

        self.health_state = {

            "pressure_score":
            0.0,

            "pressure_state":
            "stable",

            "graph_complexity":
            0,

            "retrieval_latency":
            "low"
        }

        # ====================================
        # BUS STATE
        # ====================================

        self.bus_state = {

            "bus_mode":
            "recursive_semantic_routing",

            "semantic_activation":
            "enabled",

            "priority_routing":
            "enabled",

            "adaptive_compression":
            "enabled",

            "lazy_loading":
            "enabled",

            "semantic_retrieval":
            "enabled",

            "context_consolidation":
            "enabled",

            "recursive_stabilization":
            "enabled",

            "context_stability":
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
    # COMPUTE IMPORTANCE
    # ========================================

    def compute_importance(

        self,

        key,

        value
    ):

        usage = (

            self.context_access
            .get(key, {})
            .get("usage_count", 0)
        )

        importance = 0.5

        if any(

            token in key

            for token in [

                "reasoning",
                "evaluation",
                "governance",
                "strategy",
                "trajectory",
                "execution",
                "report"
            ]
        ):

            importance += 0.30

        if isinstance(value, dict):

            importance += min(

                len(value) / 100,

                0.15
            )

        importance += min(
            usage / 50,
            0.25
        )

        importance = round(
            importance,
            4
        )

        self.context_importance[
            key
        ] = importance

        return importance

    # ========================================
    # UPDATE CONTEXT
    # ========================================

    def update_context(

        self,

        key,

        value,

        priority="medium",

        ttl=10
    ):

        importance = (

            self.compute_importance(

                key,
                value
            )
        )

        self.active_contexts[
            key
        ] = {

            "value":
            value,

            "priority":
            priority,

            "importance":
            importance,

            "ttl":
            ttl,

            "usage_count":
            0,

            "timestamp":
            str(datetime.utcnow())
        }

        self.context_priorities[
            key
        ] = priority

        self.context_history.append({

            "event":
            "context_updated",

            "key":
            key,

            "priority":
            priority,

            "importance":
            importance,

            "timestamp":
            str(datetime.utcnow())
        })

        self.register_event(

            "context_updated",

            {

                "key":
                key,

                "priority":
                priority
            }
        )

    # ========================================
    # PUBLISH CONTEXT
    # ========================================

    def publish(

        self,

        key,

        value,

        priority="medium",

        ttl=10
    ):

        self.update_context(

            key=key,

            value=value,

            priority=priority,

            ttl=ttl
        )

        return {

            "published":
            True,

            "key":
            key,

            "priority":
            priority,

            "ttl":
            ttl,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # GET VALUE
    # ========================================

    def get_value(

        self,

        key,

        default=None
    ):

        self.update_access(key)

        value = self.active_contexts.get(
            key,
            default
        )

        if isinstance(value, dict):

            if "value" in value:

                return value["value"]

        return value

    # ========================================
    # SEMANTIC RETRIEVAL
    # ========================================

    def semantic_retrieve(

        self,

        query
    ):

        matches = []

        all_contexts = {

            **self.active_contexts,

            **self.dormant_contexts
        }

        for key, value in all_contexts.items():

            score = 0.0

            if query in key:

                score += 0.7

            importance = (

                self.context_importance.get(
                    key,
                    0.0
                )
            )

            score += importance * 0.3

            if score > 0.4:

                matches.append({

                    "context":
                    key,

                    "score":
                    round(score, 4),

                    "importance":
                    importance
                })

        matches = sorted(

            matches,

            key=lambda x:
            x["score"],

            reverse=True
        )

        return matches[:10]

    # ========================================
    # RETRIEVE CONTEXT
    # ========================================

    def retrieve(

        self,

        key
    ):

        self.update_access(key)

        # ====================================
        # ACTIVE
        # ====================================

        if key in self.active_contexts:

            return self.active_contexts[
                key
            ]

        # ====================================
        # DORMANT
        # ====================================

        if key in self.dormant_contexts:

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

        # ====================================
        # ARCHIVED
        # ====================================

        if key in self.archived_contexts:

            return self.archived_contexts[
                key
            ]

        return None

    # ========================================
    # FREEZE CONTEXT
    # ========================================

    def freeze(

        self,

        key
    ):

        if key not in self.active_contexts:

            return False

        context = self.active_contexts.pop(
            key
        )

        context[
            "frozen_at"
        ] = str(
            datetime.utcnow()
        )

        self.dormant_contexts[
            key
        ] = context

        self.register_event(

            "context_frozen",

            {

                "context":
                key
            }
        )

        return True

    # ========================================
    # ARCHIVE CONTEXT
    # ========================================

    def archive(

        self,

        key
    ):

        if key in self.active_contexts:

            context = self.active_contexts.pop(
                key
            )

            context[
                "archived_at"
            ] = str(
                datetime.utcnow()
            )

            self.archived_contexts[
                key
            ] = context

            return True

        if key in self.dormant_contexts:

            context = self.dormant_contexts.pop(
                key
            )

            context[
                "archived_at"
            ] = str(
                datetime.utcnow()
            )

            self.archived_contexts[
                key
            ] = context

            return True

        return False

    # ========================================
    # ACTIVATE CONTEXT
    # ========================================

    def activate(

        self,

        key
    ):

        if key not in self.dormant_contexts:

            return False

        self.active_contexts[
            key
        ] = self.dormant_contexts.pop(
            key
        )

        return True

    # ========================================
    # SEMANTIC CONSOLIDATION
    # ========================================

    def consolidate_contexts(self):

        grouped = {}

        for key in self.active_contexts:

            prefix = key.split("_")[0]

            if prefix not in grouped:

                grouped[prefix] = []

            grouped[prefix].append(key)

        self.consolidated_contexts = grouped

        return {

            "groups":
            grouped,

            "group_count":
            len(grouped),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # COMPRESS CONTEXTS
    # ========================================

    def compress_contexts(

        self,

        max_active=64
    ):

        if len(self.active_contexts) <= max_active:

            return {

                "compression":
                False,

                "active_contexts":
                len(self.active_contexts)
            }

        sorted_contexts = sorted(

            self.active_contexts.items(),

            key=lambda item:

            self.context_importance.get(
                item[0],
                0.0
            )
        )

        compressed = []

        while len(self.active_contexts) > max_active:

            key, _ = sorted_contexts.pop(0)

            self.freeze(key)

            compressed.append(key)

        return {

            "compression":
            True,

            "compressed_contexts":
            compressed,

            "remaining_active":
            len(self.active_contexts)
        }

    # ========================================
    # CONTEXT TTL MANAGEMENT
    # ========================================

    def update_ttl(self):

        expired = []

        for key in list(

            self.active_contexts.keys()
        ):

            self.active_contexts[
                key
            ][
                "ttl"
            ] -= 1

            ttl = self.active_contexts[
                key
            ][
                "ttl"
            ]

            if ttl <= 0:

                self.freeze(key)

                expired.append(key)

        return {

            "expired_contexts":
            expired,

            "expired_count":
            len(expired)
        }

    # ========================================
    # BUILD CONTEXT GRAPH
    # ========================================

    def build_context_graph(self):

        nodes = []

        edges = []

        node_id = 0

        all_contexts = []

        for key in self.active_contexts:

            all_contexts.append(
                (key, "active")
            )

        for key in self.dormant_contexts:

            all_contexts.append(
                (key, "dormant")
            )

        for key in self.archived_contexts:

            all_contexts.append(
                (key, "archived")
            )

        node_map = {}

        for context_key, state in all_contexts:

            nodes.append({

                "node_id":
                node_id,

                "context":
                context_key,

                "state":
                state,

                "importance":

                self.context_importance.get(
                    context_key,
                    0.0
                )
            })

            node_map[
                context_key
            ] = node_id

            node_id += 1

        for source_key in node_map:

            for target_key in node_map:

                if source_key == target_key:

                    continue

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
                        node_map[source_key],

                        "target":
                        node_map[target_key],

                        "relation":
                        "semantic_association",

                        "relation_weight":
                        shared
                    })

        return {

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "recursive_semantic_graph"
        }

    # ========================================
    # HEALTH MONITOR
    # ========================================

    def health_monitor(self):

        graph = self.build_context_graph()

        total_contexts = (

            len(self.active_contexts)

            +

            len(self.dormant_contexts)

            +

            len(self.archived_contexts)
        )

        pressure_score = round(

            min(
                total_contexts / 500,
                1.0
            ),

            4
        )

        graph_complexity = len(
            graph["edges"]
        )

        if pressure_score >= 0.85:

            pressure_state = "critical"

        elif pressure_score >= 0.60:

            pressure_state = "elevated"

        else:

            pressure_state = "stable"

        self.health_state = {

            "pressure_score":
            pressure_score,

            "pressure_state":
            pressure_state,

            "graph_complexity":
            graph_complexity,

            "retrieval_latency":

            "high"

            if graph_complexity > 5000

            else "low"
        }

        return self.health_state

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        graph = self.build_context_graph()

        return {

            "bus_state":
            self.bus_state,

            "active_contexts":
            len(self.active_contexts),

            "dormant_contexts":
            len(self.dormant_contexts),

            "archived_contexts":
            len(self.archived_contexts),

            "context_cycles":
            len(self.context_history),

            "context_events":
            len(self.context_events),

            "context_graph_nodes":
            len(graph["nodes"]),

            "context_graph_edges":
            len(graph["edges"]),

            "health_state":
            self.health_state,

            "consolidated_groups":
            len(self.consolidated_contexts),

            "system_state":
            "stable"
        }


# ============================================
# GLOBAL CONTEXT BUS
# ============================================

context_bus = (
    ContextBus()
)