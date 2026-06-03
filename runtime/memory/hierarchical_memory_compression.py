# ============================================
# NEXRYN HIERARCHICAL MEMORY COMPRESSION
# ============================================

from datetime import datetime

import copy


# ============================================
# HIERARCHICAL MEMORY COMPRESSION
# ============================================

class HierarchicalMemoryCompression:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # ACTIVE MEMORY
        # ====================================

        self.active_memory = {}

        # ====================================
        # SHORT TERM MEMORY
        # ====================================

        self.short_term_memory = []

        # ====================================
        # SEMANTIC MEMORY
        # ====================================

        self.semantic_memory = []

        # ====================================
        # COMPRESSED MEMORY
        # ====================================

        self.compressed_memory = []

        # ====================================
        # ARCHIVAL MEMORY
        # ====================================

        self.archival_memory = []

        # ====================================
        # CONFIGURATION
        # ====================================

        self.configuration = {

            "max_short_term":
            25,

            "max_semantic":
            50,

            "max_compressed":
            100,

            "compression_enabled":
            True,

            "semantic_abstraction":
            True,

            "hierarchical_storage":
            True
        }

        # ====================================
        # METRICS
        # ====================================

        self.metrics = {

            "compression_cycles":
            0,

            "compressed_contexts":
            0,

            "semantic_extractions":
            0,

            "archived_contexts":
            0
        }

    # ========================================
    # EXTRACT SEMANTIC MEMORY
    # ========================================

    def extract_semantic_memory(

        self,

        runtime_context
    ):

        semantic_snapshot = {

            "semantic_abstractions":

            runtime_context.get(
                "semantic_abstractions",
                []
            ),

            "winner_hypothesis":

            runtime_context.get(
                "winner_hypothesis",
                {}
            ),

            "best_path":

            runtime_context.get(
                "best_path",
                {}
            ),

            "reasoning_depth":

            runtime_context.get(
                "inference_report",
                {}
            ).get(
                "reasoning_depth",
                0
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.semantic_memory.append(
            semantic_snapshot
        )

        self.metrics[
            "semantic_extractions"
        ] += 1

        return semantic_snapshot

    # ========================================
    # COMPRESS CONTEXT
    # ========================================

    def compress_context(

        self,

        runtime_context
    ):

        compressed_context = {

            "task_path":

            runtime_context.get(
                "task_path"
            ),

            "winner_hypothesis":

            runtime_context.get(
                "winner_hypothesis"
            ),

            "evaluation_result":

            runtime_context.get(
                "evaluation_result"
            ),

            "execution_metrics":

            runtime_context.get(
                "execution_metrics"
            ),

            "runtime_metadata":

            runtime_context.get(
                "runtime_metadata"
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.compressed_memory.append(
            compressed_context
        )

        self.metrics[
            "compressed_contexts"
        ] += 1

        return compressed_context

    # ========================================
    # ARCHIVE CONTEXT
    # ========================================

    def archive_context(

        self,

        runtime_context
    ):

        archive_snapshot = {

            "task_path":

            runtime_context.get(
                "task_path"
            ),

            "context_size":
            len(runtime_context),

            "runtime_status":

            runtime_context.get(
                "runtime_metadata",
                {}
            ).get(
                "runtime_status",
                "unknown"
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.archival_memory.append(
            archive_snapshot
        )

        self.metrics[
            "archived_contexts"
        ] += 1

        return archive_snapshot

    # ========================================
    # MEMORY CYCLE
    # ========================================

    def run_compression_cycle(

        self,

        runtime_context
    ):

        self.active_memory = (
            copy.deepcopy(
                runtime_context
            )
        )

        self.short_term_memory.append({

            "task_path":

            runtime_context.get(
                "task_path"
            ),

            "timestamp":
            str(datetime.utcnow())
        })

        semantic_snapshot = (

            self.extract_semantic_memory(
                runtime_context
            )
        )

        compressed_context = (

            self.compress_context(
                runtime_context
            )
        )

        archive_snapshot = (

            self.archive_context(
                runtime_context
            )
        )

        # ====================================
        # SHORT TERM LIMIT
        # ====================================

        max_short_term = (

            self.configuration.get(
                "max_short_term",
                25
            )
        )

        if len(
            self.short_term_memory
        ) > max_short_term:

            self.short_term_memory = (

                self.short_term_memory[
                    -max_short_term:
                ]
            )

        # ====================================
        # METRICS
        # ====================================

        self.metrics[
            "compression_cycles"
        ] += 1

        compression_report = {

            "active_memory_size":

            len(
                self.active_memory
            ),

            "short_term_entries":

            len(
                self.short_term_memory
            ),

            "semantic_entries":

            len(
                self.semantic_memory
            ),

            "compressed_entries":

            len(
                self.compressed_memory
            ),

            "archival_entries":

            len(
                self.archival_memory
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        return {

            "semantic_snapshot":
            semantic_snapshot,

            "compressed_context":
            compressed_context,

            "archive_snapshot":
            archive_snapshot,

            "compression_report":
            compression_report
        }

    # ========================================
    # SUMMARY
    # ========================================

    def summary(self):

        return {

            "metrics":
            self.metrics,

            "active_memory_size":

            len(
                self.active_memory
            ),

            "short_term_memory":

            len(
                self.short_term_memory
            ),

            "semantic_memory":

            len(
                self.semantic_memory
            ),

            "compressed_memory":

            len(
                self.compressed_memory
            ),

            "archival_memory":

            len(
                self.archival_memory
            )
        }


# ============================================
# GLOBAL ENGINE
# ============================================

hierarchical_memory_compression = (
    HierarchicalMemoryCompression()
)