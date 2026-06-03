# ============================================
# NEXRYN MEMORY CONSOLIDATION ENGINE
# ============================================

from datetime import datetime

import copy


# ============================================
# MEMORY CONSOLIDATION ENGINE
# ============================================

class MemoryConsolidationEngine:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # CONSOLIDATED MEMORIES
        # ====================================

        self.consolidated_memories = []

        # ====================================
        # SEMANTIC CLUSTERS
        # ====================================

        self.semantic_clusters = {}

        # ====================================
        # ARCHIVED MEMORIES
        # ====================================

        self.archived_memories = []

        # ====================================
        # ENGINE CONFIGURATION
        # ====================================

        self.configuration = {

            "semantic_merging":
            True,

            "duplicate_removal":
            True,

            "adaptive_archiving":
            True,

            "importance_filtering":
            True,

            "memory_compression":
            True
        }

        # ====================================
        # METRICS
        # ====================================

        self.metrics = {

            "consolidation_cycles":
            0,

            "merged_memories":
            0,

            "archived_memories":
            0,

            "semantic_clusters":
            0,

            "duplicates_removed":
            0
        }

    # ========================================
    # COMPUTE IMPORTANCE SCORE
    # ========================================

    def compute_importance_score(

        self,

        memory
    ):

        score = 0.0

        evaluation_result = (

            memory.get(
                "evaluation_result",
                {}
            )
        )

        if evaluation_result.get(
            "success"
        ):

            score += 0.5

        reasoning_depth = (

            memory.get(
                "inference_report",
                {}
            ).get(
                "reasoning_depth",
                0
            )
        )

        score += min(
            reasoning_depth / 20,
            0.3
        )

        semantic_count = len(

            memory.get(
                "semantic_abstractions",
                []
            )
        )

        score += min(
            semantic_count / 10,
            0.2
        )

        return round(
            score,
            4
        )

    # ========================================
    # GENERATE MEMORY SIGNATURE
    # ========================================

    def generate_signature(

        self,

        memory
    ):

        winner = (

            memory.get(
                "winner_hypothesis",
                {}
            )
        )

        hypothesis_type = (

            winner.get(
                "type",
                "unknown"
            )
        )

        semantic_concepts = [

            abstraction.get(
                "semantic_concept",
                "unknown"
            )

            for abstraction in (

                memory.get(
                    "semantic_abstractions",
                    []
                )
            )
        ]

        semantic_concepts = sorted(
            semantic_concepts
        )

        return (

            f"{hypothesis_type}"
            f"::"
            f"{'-'.join(semantic_concepts)}"
        )

    # ========================================
    # REMOVE DUPLICATES
    # ========================================

    def remove_duplicates(

        self,

        memories
    ):

        unique_memories = []

        signatures = set()

        duplicate_count = 0

        for memory in memories:

            signature = (

                self.generate_signature(
                    memory
                )
            )

            if signature not in signatures:

                signatures.add(
                    signature
                )

                unique_memories.append(
                    memory
                )

            else:

                duplicate_count += 1

        self.metrics[
            "duplicates_removed"
        ] += duplicate_count

        return unique_memories

    # ========================================
    # BUILD SEMANTIC CLUSTERS
    # ========================================

    def build_semantic_clusters(

        self,

        memories
    ):

        clusters = {}

        for memory in memories:

            abstractions = (

                memory.get(
                    "semantic_abstractions",
                    []
                )
            )

            for abstraction in abstractions:

                concept = (

                    abstraction.get(
                        "semantic_concept",
                        "unknown"
                    )
                )

                if concept not in clusters:

                    clusters[concept] = []

                clusters[
                    concept
                ].append(
                    memory
                )

        self.semantic_clusters = (
            clusters
        )

        self.metrics[
            "semantic_clusters"
        ] = len(
            clusters
        )

        return clusters

    # ========================================
    # CONSOLIDATE MEMORIES
    # ========================================

    def consolidate_memories(

        self,

        memories
    ):

        if not memories:

            return {

                "consolidated_memories":
                [],

                "consolidation_report":
                {}
            }

        memories = (
            self.remove_duplicates(
                memories
            )
        )

        semantic_clusters = (

            self.build_semantic_clusters(
                memories
            )
        )

        consolidated = []

        archived = []

        for memory in memories:

            importance_score = (

                self.compute_importance_score(
                    memory
                )
            )

            memory_snapshot = {

                "task_path":

                memory.get(
                    "task_path"
                ),

                "winner_hypothesis":

                memory.get(
                    "winner_hypothesis"
                ),

                "semantic_abstractions":

                memory.get(
                    "semantic_abstractions",
                    []
                ),

                "evaluation_result":

                memory.get(
                    "evaluation_result",
                    {}
                ),

                "importance_score":
                importance_score,

                "timestamp":
                str(datetime.utcnow())
            }

            if importance_score >= 0.6:

                consolidated.append(
                    memory_snapshot
                )

            else:

                archived.append(
                    memory_snapshot
                )

        self.consolidated_memories.extend(
            consolidated
        )

        self.archived_memories.extend(
            archived
        )

        self.metrics[
            "consolidation_cycles"
        ] += 1

        self.metrics[
            "merged_memories"
        ] += len(
            consolidated
        )

        self.metrics[
            "archived_memories"
        ] += len(
            archived
        )

        consolidation_report = {

            "input_memories":
            len(memories),

            "consolidated":
            len(consolidated),

            "archived":
            len(archived),

            "semantic_clusters":
            len(semantic_clusters),

            "timestamp":
            str(datetime.utcnow())
        }

        return {

            "consolidated_memories":
            consolidated,

            "archived_memories":
            archived,

            "semantic_clusters":
            semantic_clusters,

            "consolidation_report":
            consolidation_report
        }

    # ========================================
    # BUILD MEMORY SUMMARY
    # ========================================

    def build_memory_summary(self):

        dominant_clusters = []

        for concept, memories in (
            self.semantic_clusters.items()
        ):

            dominant_clusters.append({

                "concept":
                concept,

                "memory_count":
                len(memories)
            })

        dominant_clusters = sorted(

            dominant_clusters,

            key=lambda x:
            x["memory_count"],

            reverse=True
        )

        return {

            "dominant_clusters":
            dominant_clusters[:10],

            "consolidated_memory_count":

            len(
                self.consolidated_memories
            ),

            "archived_memory_count":

            len(
                self.archived_memories
            )
        }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "metrics":
            self.metrics,

            "consolidated_memories":

            len(
                self.consolidated_memories
            ),

            "archived_memories":

            len(
                self.archived_memories
            ),

            "semantic_clusters":

            len(
                self.semantic_clusters
            ),

            "memory_summary":

            self.build_memory_summary()
        }


# ============================================
# GLOBAL ENGINE
# ============================================

memory_consolidation_engine = (
    MemoryConsolidationEngine()
)