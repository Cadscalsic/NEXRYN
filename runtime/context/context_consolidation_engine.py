# ============================================
# NEXRYN CONTEXT CONSOLIDATION ENGINE
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# CONTEXT CONSOLIDATION ENGINE
# ============================================

class ContextConsolidationEngine:

    # ========================================
    # INITIALIZE ENGINE
    # ========================================

    def __init__(self):

        # ====================================
        # CONSOLIDATED MEMORY
        # ====================================

        self.consolidated_memory = {}

        # ====================================
        # CONSOLIDATION HISTORY
        # ====================================

        self.consolidation_history = []

        # ====================================
        # SEMANTIC GROUPS
        # ====================================

        self.semantic_groups = {}

        # ====================================
        # ABSTRACTION MEMORY
        # ====================================

        self.abstraction_memory = []

        # ====================================
        # DUPLICATE MEMORY
        # ====================================

        self.duplicate_memory = []

        # ====================================
        # RECURSIVE GROUPS
        # ====================================

        self.recursive_groups = []

        # ====================================
        # EXECUTIVE GROUPS
        # ====================================

        self.executive_groups = []

        # ====================================
        # EVENTS
        # ====================================

        self.events = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "consolidation_mode":
            "recursive_semantic_consolidation",

            "semantic_merging":
            "enabled",

            "duplicate_detection":
            "enabled",

            "abstraction_generation":
            "enabled",

            "recursive_grouping":
            "enabled",

            "executive_awareness":
            "enabled",

            "adaptive_memory_compression":
            "enabled",

            "consolidation_cycles":
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
    # TOKENIZE CONTEXT
    # ========================================

    def tokenize_context(

        self,

        context_key
    ):

        tokens = (

            context_key
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
    # COMPUTE SIMILARITY
    # ========================================

    def compute_similarity(

        self,

        source_key,

        target_key
    ):

        source_tokens = (

            self.tokenize_context(
                source_key
            )
        )

        target_tokens = (

            self.tokenize_context(
                target_key
            )
        )

        shared = len(

            set(source_tokens)
            .intersection(

                set(target_tokens)
            )
        )

        total = max(

            len(
                set(source_tokens)
                .union(
                    set(target_tokens)
                )
            ),

            1
        )

        similarity = round(

            shared / total,

            4
        )

        return similarity

    # ========================================
    # DETECT DUPLICATES
    # ========================================

    def detect_duplicates(

        self,

        contexts,

        threshold=0.75
    ):

        duplicates = []

        keys = list(
            contexts.keys()
        )

        for source_index in range(

            len(keys)
        ):

            for target_index in range(

                source_index + 1,

                len(keys)
            ):

                source_key = keys[
                    source_index
                ]

                target_key = keys[
                    target_index
                ]

                similarity = (

                    self.compute_similarity(

                        source_key,
                        target_key
                    )
                )

                if similarity >= threshold:

                    duplicate = {

                        "source":
                        source_key,

                        "target":
                        target_key,

                        "similarity":
                        similarity
                    }

                    duplicates.append(
                        duplicate
                    )

        self.duplicate_memory.extend(
            duplicates
        )

        return duplicates

    # ========================================
    # BUILD SEMANTIC GROUPS
    # ========================================

    def build_semantic_groups(

        self,

        contexts
    ):

        self.semantic_groups = {}

        for context_key in contexts:

            tokens = self.tokenize_context(
                context_key
            )

            if len(tokens) == 0:

                continue

            root = tokens[0]

            if root not in self.semantic_groups:

                self.semantic_groups[
                    root
                ] = []

            self.semantic_groups[
                root
            ].append(
                context_key
            )

        return self.semantic_groups

    # ========================================
    # DETECT RECURSIVE GROUPS
    # ========================================

    def detect_recursive_groups(self):

        recursive_tokens = [

            "recursive",
            "meta",
            "cycle",
            "reflection",
            "loop",
            "self"
        ]

        groups = []

        for group, members in (

            self.semantic_groups.items()
        ):

            for token in recursive_tokens:

                if token in group:

                    groups.append({

                        "group":
                        group,

                        "members":
                        members
                    })

        self.recursive_groups = groups

        return groups

    # ========================================
    # DETECT EXECUTIVE GROUPS
    # ========================================

    def detect_executive_groups(self):

        executive_tokens = [

            "goal",
            "governance",
            "planning",
            "strategy",
            "mission",
            "executive"
        ]

        groups = []

        for group, members in (

            self.semantic_groups.items()
        ):

            for token in executive_tokens:

                if token in group:

                    groups.append({

                        "group":
                        group,

                        "members":
                        members
                    })

        self.executive_groups = groups

        return groups

    # ========================================
    # GENERATE ABSTRACTION
    # ========================================

    def generate_abstraction(

        self,

        group_name,

        members
    ):

        abstraction = {

            "abstraction_id":
            str(uuid.uuid4()),

            "group":
            group_name,

            "member_count":
            len(members),

            "members":
            members[:10],

            "abstraction_type":
            "semantic_context_abstraction",

            "generated_at":
            str(datetime.utcnow())
        }

        self.abstraction_memory.append(
            abstraction
        )

        return abstraction

    # ========================================
    # CONSOLIDATE GROUPS
    # ========================================

    def consolidate_groups(self):

        consolidated = {}

        for group, members in (

            self.semantic_groups.items()
        ):

            abstraction = (

                self.generate_abstraction(

                    group,
                    members
                )
            )

            consolidated[
                group
            ] = {

                "members":
                members,

                "abstraction":
                abstraction
            }

        self.consolidated_memory = (
            consolidated
        )

        return consolidated

    # ========================================
    # COMPRESS CONTEXT MEMORY
    # ========================================

    def compress_context_memory(

        self,

        context_bus,

        importance_engine=None
    ):

        compressed = []

        active_contexts = (

            context_bus.active_contexts
        )

        if importance_engine is None:

            return []

        sorted_contexts = sorted(

            active_contexts.items(),

            key=lambda item:

            importance_engine
            .importance_memory
            .get(

                item[0],
                0.0
            )
        )

        overflow = max(

            0,

            len(active_contexts) - 64
        )

        for key, _ in sorted_contexts[:overflow]:

            context_bus.freeze(
                key
            )

            compressed.append(
                key
            )

        return compressed

    # ========================================
    # BUILD CONSOLIDATION GRAPH
    # ========================================

    def build_consolidation_graph(self):

        nodes = []

        edges = []

        node_id = 0

        node_map = {}

        for group, data in (

            self.consolidated_memory.items()
        ):

            nodes.append({

                "node_id":
                node_id,

                "group":
                group,

                "member_count":

                len(
                    data.get(
                        "members",
                        []
                    )
                )
            })

            node_map[group] = node_id

            node_id += 1

        groups = list(
            node_map.keys()
        )

        for source in range(

            len(groups)
        ):

            for target in range(

                source + 1,

                len(groups)
            ):

                source_group = groups[
                    source
                ]

                target_group = groups[
                    target
                ]

                similarity = (

                    self.compute_similarity(

                        source_group,
                        target_group
                    )
                )

                if similarity > 0:

                    edges.append({

                        "source":
                        node_map[source_group],

                        "target":
                        node_map[target_group],

                        "relation":
                        "semantic_consolidation",

                        "weight":
                        similarity
                    })

        return {

            "nodes":
            nodes,

            "edges":
            edges,

            "graph_mode":
            "recursive_consolidation_graph"
        }

    # ========================================
    # RUN CONSOLIDATION CYCLE
    # ========================================

    def run_consolidation_cycle(

        self,

        context_bus,

        importance_engine=None
    ):

        # ====================================
        # BUILD CONTEXT POOL
        # ====================================

        contexts = {

            **context_bus.active_contexts,

            **context_bus.dormant_contexts
        }

        # ====================================
        # DUPLICATE DETECTION
        # ====================================

        duplicates = (

            self.detect_duplicates(
                contexts
            )
        )

        # ====================================
        # BUILD GROUPS
        # ====================================

        semantic_groups = (

            self.build_semantic_groups(
                contexts
            )
        )

        # ====================================
        # RECURSIVE GROUPS
        # ====================================

        recursive_groups = (

            self.detect_recursive_groups()
        )

        # ====================================
        # EXECUTIVE GROUPS
        # ====================================

        executive_groups = (

            self.detect_executive_groups()
        )

        # ====================================
        # CONSOLIDATION
        # ====================================

        consolidated = (

            self.consolidate_groups()
        )

        # ====================================
        # MEMORY COMPRESSION
        # ====================================

        compressed = (

            self.compress_context_memory(

                context_bus,

                importance_engine
            )
        )

        # ====================================
        # GRAPH
        # ====================================

        consolidation_graph = (

            self.build_consolidation_graph()
        )

        self.engine_state[
            "consolidation_cycles"
        ] += 1

        report = {

            "duplicates":
            duplicates,

            "semantic_groups":
            semantic_groups,

            "recursive_groups":
            recursive_groups,

            "executive_groups":
            executive_groups,

            "consolidated_memory":
            consolidated,

            "compressed_contexts":
            compressed,

            "consolidation_graph":
            consolidation_graph,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.consolidation_history.append(
            report
        )

        self.register_event(

            "consolidation_cycle",

            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        consolidation_graph = (
            self.build_consolidation_graph()
        )

        return {

            "engine_state":
            self.engine_state,

            "consolidated_memory":
            len(self.consolidated_memory),

            "consolidation_history":
            len(self.consolidation_history),

            "semantic_groups":
            len(self.semantic_groups),

            "abstraction_memory":
            len(self.abstraction_memory),

            "duplicate_memory":
            len(self.duplicate_memory),

            "recursive_groups":
            len(self.recursive_groups),

            "executive_groups":
            len(self.executive_groups),

            "events":
            len(self.events),

            "consolidation_graph_nodes":
            len(
                consolidation_graph["nodes"]
            ),

            "consolidation_graph_edges":
            len(
                consolidation_graph["edges"]
            ),

            "latest_cycle":

            self.consolidation_history[-1]

            if self.consolidation_history

            else {}
        }


# ============================================
# GLOBAL CONSOLIDATION ENGINE
# ============================================

context_consolidation_engine = (
    ContextConsolidationEngine()
)