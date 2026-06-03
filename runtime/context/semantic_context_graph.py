# ============================================
# NEXRYN SEMANTIC CONTEXT GRAPH
# ============================================

from datetime import datetime
import uuid
import math


# ============================================
# SEMANTIC CONTEXT GRAPH
# ============================================

class SemanticContextGraph:

    # ========================================
    # INITIALIZE GRAPH
    # ========================================

    def __init__(self):

        # ====================================
        # GRAPH STRUCTURE
        # ====================================

        self.nodes = []

        self.edges = []

        self.node_map = {}

        # ====================================
        # GRAPH HISTORY
        # ====================================

        self.graph_history = []

        # ====================================
        # GRAPH EVENTS
        # ====================================

        self.graph_events = []

        # ====================================
        # SEMANTIC CLUSTERS
        # ====================================

        self.semantic_clusters = {}

        # ====================================
        # RECURSIVE CLUSTERS
        # ====================================

        self.recursive_clusters = []

        # ====================================
        # EXECUTIVE CLUSTERS
        # ====================================

        self.executive_clusters = []

        # ====================================
        # STABILITY CLUSTERS
        # ====================================

        self.stability_clusters = []

        # ====================================
        # GRAPH STATE
        # ====================================

        self.graph_state = {

            "graph_mode":
            "recursive_semantic_context_graph",

            "semantic_linking":
            "enabled",

            "dependency_tracking":
            "enabled",

            "recursive_topology":
            "enabled",

            "executive_awareness":
            "enabled",

            "stability_monitoring":
            "enabled",

            "adaptive_pruning":
            "enabled",

            "incremental_graph_updates":
            "enabled",

            "graph_cycles":
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

        self.graph_events.append(
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

        context_key = str(
            context_key
        )

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
    # COMPUTE SEMANTIC SIMILARITY
    # ========================================

    def compute_semantic_similarity(

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
    # DETECT RELATION TYPE
    # ========================================

    def detect_relation_type(

        self,

        source_key,

        target_key
    ):

        source_key = str(
            source_key
        )

        if "reasoning" in source_key:

            return "reasoning_dependency"

        if "strategy" in source_key:

            return "executive_dependency"

        if "recursive" in source_key:

            return "recursive_association"

        if "memory" in source_key:

            return "memory_association"

        if "governance" in source_key:

            return "governance_association"

        return "semantic_association"

    # ========================================
    # REGISTER NODE
    # ========================================

    def register_node(

        self,

        context_key,

        importance=0.5
    ):

        if context_key is None:

            context_key = "undefined"

        if not isinstance(
            context_key,
            str
        ):

            context_key = str(
                context_key
            )

        # ====================================
        # ALREADY REGISTERED
        # ====================================

        if context_key in self.node_map:

            node_id = self.node_map[
                context_key
            ]

            if node_id < len(self.nodes):

                existing_node = self.nodes[
                    node_id
                ]

                existing_node[
                    "activation_count"
                ] += 1

                return existing_node

        # ====================================
        # CREATE NODE
        # ====================================

        node_id = len(self.nodes)

        node = {

            "node_id":
            node_id,

            "context_key":
            context_key,

            "importance":
            importance,

            "context_type":
            "runtime_context",

            "activation_count":
            1,

            "relationship_count":
            0,

            "semantic_weight":
            importance,

            "timestamp":
            str(datetime.utcnow())
        }

        self.nodes.append(
            node
        )

        self.node_map[
            context_key
        ] = node_id

        return node

    # ========================================
    # CREATE EDGE
    # ========================================

    def create_edge(

        self,

        source_key,

        target_key,

        relation=None
    ):

        if source_key is None:

            return None

        if target_key is None:

            return None

        source_key = str(
            source_key
        )

        target_key = str(
            target_key
        )

        # ====================================
        # REGISTER NODES
        # ====================================

        source_node = self.register_node(
            source_key
        )

        target_node = self.register_node(
            target_key
        )

        # ====================================
        # AUTO RELATION
        # ====================================

        if relation is None:

            relation = (

                self.detect_relation_type(

                    source_key,

                    target_key
                )
            )

        # ====================================
        # SIMILARITY
        # ====================================

        similarity = (

            self.compute_semantic_similarity(

                source_key,

                target_key
            )
        )

        # ====================================
        # DUPLICATE CHECK
        # ====================================

        for edge in self.edges:

            if (

                edge.get(
                    "source_key"
                ) == source_key

                and

                edge.get(
                    "target_key"
                ) == target_key
            ):

                return edge

        # ====================================
        # CREATE EDGE
        # ====================================

        edge = {

            "edge_id":
            str(uuid.uuid4()),

            "source":
            source_node[
                "node_id"
            ],

            "target":
            target_node[
                "node_id"
            ],

            "source_key":
            source_key,

            "target_key":
            target_key,

            "relation":
            relation,

            "semantic_similarity":
            similarity,

            "relation_weight":
            round(
                similarity * 10,
                4
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.edges.append(
            edge
        )

        # ====================================
        # UPDATE COUNTERS
        # ====================================

        source_node[
            "relationship_count"
        ] += 1

        target_node[
            "relationship_count"
        ] += 1

        return edge

    # ========================================
    # BUILD NODES
    # ========================================

    def build_nodes(

        self,

        contexts,

        importance_engine=None
    ):

        self.nodes = []

        self.node_map = {}

        for context_key, context in (

            contexts.items()
        ):

            importance = 0.5

            if (

                importance_engine is not None

                and

                hasattr(
                    importance_engine,
                    "importance_memory"
                )
            ):

                importance = (

                    importance_engine
                    .importance_memory
                    .get(
                        context_key,
                        0.5
                    )
                )

            self.register_node(

                context_key,

                importance
            )

        return self.nodes

    # ========================================
    # BUILD EDGES
    # ========================================

    def build_edges(

        self,

        similarity_threshold=0.20
    ):

        self.edges = []

        context_keys = list(
            self.node_map.keys()
        )

        for source_index in range(

            len(context_keys)
        ):

            for target_index in range(

                source_index + 1,

                len(context_keys)
            ):

                source_key = context_keys[
                    source_index
                ]

                target_key = context_keys[
                    target_index
                ]

                similarity = (

                    self.compute_semantic_similarity(

                        source_key,
                        target_key
                    )
                )

                if similarity >= similarity_threshold:

                    self.create_edge(

                        source_key,

                        target_key
                    )

        return self.edges

    # ========================================
    # BUILD SEMANTIC CLUSTERS
    # ========================================

    def build_semantic_clusters(self):

        self.semantic_clusters = {}

        for node in self.nodes:

            context_key = node[
                "context_key"
            ]

            tokens = self.tokenize_context(
                context_key
            )

            if len(tokens) == 0:

                continue

            cluster = tokens[0]

            if cluster not in (

                self.semantic_clusters
            ):

                self.semantic_clusters[
                    cluster
                ] = []

            self.semantic_clusters[
                cluster
            ].append(
                context_key
            )

        return self.semantic_clusters

    # ========================================
    # DETECT RECURSIVE CLUSTERS
    # ========================================

    def detect_recursive_clusters(self):

        recursive_tokens = [

            "recursive",
            "meta",
            "reflection",
            "loop",
            "cycle",
            "self"
        ]

        clusters = []

        for cluster, members in (

            self.semantic_clusters.items()
        ):

            for token in recursive_tokens:

                if token in cluster:

                    clusters.append({

                        "cluster":
                        cluster,

                        "members":
                        members
                    })

        self.recursive_clusters = (
            clusters
        )

        return clusters

    # ========================================
    # DETECT EXECUTIVE CLUSTERS
    # ========================================

    def detect_executive_clusters(self):

        executive_tokens = [

            "goal",
            "strategy",
            "governance",
            "planning",
            "mission",
            "executive"
        ]

        clusters = []

        for cluster, members in (

            self.semantic_clusters.items()
        ):

            for token in executive_tokens:

                if token in cluster:

                    clusters.append({

                        "cluster":
                        cluster,

                        "members":
                        members
                    })

        self.executive_clusters = (
            clusters
        )

        return clusters

    # ========================================
    # DETECT STABILITY CLUSTERS
    # ========================================

    def detect_stability_clusters(self):

        stability_tokens = [

            "stability",
            "compression",
            "health",
            "governor",
            "pressure",
            "recovery"
        ]

        clusters = []

        for cluster, members in (

            self.semantic_clusters.items()
        ):

            for token in stability_tokens:

                if token in cluster:

                    clusters.append({

                        "cluster":
                        cluster,

                        "members":
                        members
                    })

        self.stability_clusters = (
            clusters
        )

        return clusters

    # ========================================
    # COMPUTE GRAPH DENSITY
    # ========================================

    def compute_graph_density(self):

        node_count = len(self.nodes)

        edge_count = len(self.edges)

        density = round(

            edge_count
            /
            max(node_count, 1),

            4
        )

        return density

    # ========================================
    # ANALYZE GRAPH HEALTH
    # ========================================

    def analyze_graph_health(self):

        density = (
            self.compute_graph_density()
        )

        edge_count = len(self.edges)

        if edge_count >= 10000:

            graph_state = "critical"

        elif edge_count >= 5000:

            graph_state = "high"

        elif edge_count >= 1000:

            graph_state = "medium"

        else:

            graph_state = "stable"

        return {

            "graph_density":
            density,

            "edge_count":
            edge_count,

            "node_count":
            len(self.nodes),

            "graph_state":
            graph_state,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # PRUNE GRAPH
    # ========================================

    def prune_graph(

        self,

        threshold=0.25
    ):

        retained_edges = []

        pruned = 0

        for edge in self.edges:

            if edge[

                "semantic_similarity"

            ] >= threshold:

                retained_edges.append(
                    edge
                )

            else:

                pruned += 1

        self.edges = retained_edges

        return {

            "pruned_edges":
            pruned,

            "remaining_edges":
            len(self.edges),

            "threshold":
            threshold,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # BUILD GRAPH
    # ========================================

    def build_graph(

        self,

        contexts,

        importance_engine=None
    ):

        # ====================================
        # BUILD NODES
        # ====================================

        self.build_nodes(

            contexts,

            importance_engine
        )

        # ====================================
        # BUILD EDGES
        # ====================================

        self.build_edges()

        # ====================================
        # BUILD CLUSTERS
        # ====================================

        semantic_clusters = (

            self.build_semantic_clusters()
        )

        recursive_clusters = (

            self.detect_recursive_clusters()
        )

        executive_clusters = (

            self.detect_executive_clusters()
        )

        stability_clusters = (

            self.detect_stability_clusters()
        )

        # ====================================
        # GRAPH HEALTH
        # ====================================

        graph_health = (

            self.analyze_graph_health()
        )

        # ====================================
        # GRAPH PRUNING
        # ====================================

        pruning_report = (
            self.prune_graph()
        )

        self.graph_state[
            "graph_cycles"
        ] += 1

        report = {

            "nodes":
            self.nodes,

            "edges":
            self.edges,

            "semantic_clusters":
            semantic_clusters,

            "recursive_clusters":
            recursive_clusters,

            "executive_clusters":
            executive_clusters,

            "stability_clusters":
            stability_clusters,

            "graph_health":
            graph_health,

            "pruning_report":
            pruning_report,

            "graph_state":
            self.graph_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.graph_history.append(
            report
        )

        self.register_event(

            "graph_cycle",

            report
        )

        return report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "graph_state":
            self.graph_state,

            "nodes":
            len(self.nodes),

            "edges":
            len(self.edges),

            "graph_history":
            len(self.graph_history),

            "graph_events":
            len(self.graph_events),

            "semantic_clusters":
            len(self.semantic_clusters),

            "recursive_clusters":
            len(self.recursive_clusters),

            "executive_clusters":
            len(self.executive_clusters),

            "stability_clusters":
            len(self.stability_clusters),

            "graph_density":
            self.compute_graph_density(),

            "latest_graph":

            self.graph_history[-1]

            if self.graph_history

            else {}
        }


# ============================================
# GLOBAL GRAPH ENGINE
# ============================================

semantic_context_graph = (
    SemanticContextGraph()
)