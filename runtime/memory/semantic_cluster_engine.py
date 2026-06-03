# ============================================
# NEXRYN SEMANTIC CLUSTER ENGINE
# ============================================

from datetime import datetime

import math


# ============================================
# SEMANTIC CLUSTER ENGINE
# ============================================

class SemanticClusterEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # SEMANTIC CLUSTERS
        # ====================================

        self.semantic_clusters = {}

        # ====================================
        # CLUSTER HISTORY
        # ====================================

        self.cluster_history = []

        # ====================================
        # CONCEPT RELATIONSHIPS
        # ====================================

        self.concept_relationships = {}

        # ====================================
        # CONFIGURATION
        # ====================================

        self.configuration = {

            "adaptive_clustering":
            True,

            "concept_grouping":
            True,

            "relationship_tracking":
            True,

            "cluster_evolution":
            True,

            "semantic_hierarchy":
            True
        }

        # ====================================
        # METRICS
        # ====================================

        self.metrics = {

            "cluster_cycles":
            0,

            "clusters_created":
            0,

            "concept_links":
            0,

            "clustered_memories":
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
    # BUILD RELATIONSHIPS
    # ========================================

    def build_relationships(

        self,

        concepts
    ):

        for concept_a in concepts:

            if concept_a not in (
                self.concept_relationships
            ):

                self.concept_relationships[
                    concept_a
                ] = {}

            for concept_b in concepts:

                if concept_a == concept_b:

                    continue

                if concept_b not in (

                    self.concept_relationships[
                        concept_a
                    ]
                ):

                    self.concept_relationships[
                        concept_a
                    ][
                        concept_b
                    ] = 0

                self.concept_relationships[
                    concept_a
                ][
                    concept_b
                ] += 1

                self.metrics[
                    "concept_links"
                ] += 1

    # ========================================
    # CLUSTER MEMORY
    # ========================================

    def cluster_memory(

        self,

        memory
    ):

        concepts = (
            self.extract_concepts(
                memory
            )
        )

        self.build_relationships(
            concepts
        )

        assigned_clusters = []

        for concept in concepts:

            if concept not in (
                self.semantic_clusters
            ):

                self.semantic_clusters[
                    concept
                ] = {

                    "cluster_id":
                    concept,

                    "cluster_type":
                    "semantic_domain",

                    "memories":
                    [],

                    "related_concepts":
                    {},

                    "created_at":
                    str(datetime.utcnow())
                }

                self.metrics[
                    "clusters_created"
                ] += 1

            self.semantic_clusters[
                concept
            ][
                "memories"
            ].append(
                memory
            )

            related = (

                self.concept_relationships.get(
                    concept,
                    {}
                )
            )

            self.semantic_clusters[
                concept
            ][
                "related_concepts"
            ] = related

            assigned_clusters.append(
                concept
            )

        self.metrics[
            "clustered_memories"
        ] += 1

        cluster_report = {

            "assigned_clusters":
            assigned_clusters,

            "concept_count":
            len(concepts),

            "timestamp":
            str(datetime.utcnow())
        }

        self.cluster_history.append(
            cluster_report
        )

        return cluster_report

    # ========================================
    # RETRIEVE CLUSTER
    # ========================================

    def retrieve_cluster(

        self,

        concept
    ):

        cluster = (

            self.semantic_clusters.get(
                concept,
                {}
            )
        )

        return {

            "cluster":
            cluster,

            "cluster_found":
            bool(cluster),

            "memory_count":

            len(
                cluster.get(
                    "memories",
                    []
                )
            ),

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # BUILD ECOSYSTEM SUMMARY
    # ========================================

    def build_ecosystem_summary(self):

        ranked_clusters = []

        for concept, cluster in (

            self.semantic_clusters.items()
        ):

            ranked_clusters.append({

                "concept":
                concept,

                "memory_count":

                len(
                    cluster.get(
                        "memories",
                        []
                    )
                ),

                "related_concepts":

                len(
                    cluster.get(
                        "related_concepts",
                        {}
                    )
                )
            })

        ranked_clusters = sorted(

            ranked_clusters,

            key=lambda x:
            x["memory_count"],

            reverse=True
        )

        dominant_relationships = []

        for concept, related in (

            self.concept_relationships.items()
        ):

            sorted_related = sorted(

                related.items(),

                key=lambda x:
                x[1],

                reverse=True
            )

            dominant_relationships.append({

                "concept":
                concept,

                "top_relationships":
                sorted_related[:5]
            })

        return {

            "dominant_clusters":
            ranked_clusters[:10],

            "relationship_ecosystem":
            dominant_relationships[:10]
        }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "metrics":
            self.metrics,

            "cluster_count":

            len(
                self.semantic_clusters
            ),

            "relationship_count":

            len(
                self.concept_relationships
            ),

            "cluster_history":

            len(
                self.cluster_history
            ),

            "ecosystem_summary":

            self.build_ecosystem_summary()
        }


# ============================================
# GLOBAL ENGINE
# ============================================

semantic_cluster_engine = (
    SemanticClusterEngine()
)