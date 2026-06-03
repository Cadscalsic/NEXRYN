# ============================================
# NEXRYN STRATEGY GARBAGE COLLECTOR
# ============================================

import gc

from datetime import datetime


# ============================================
# STRATEGY GARBAGE COLLECTOR
# ============================================

class StrategyGarbageCollector:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # MEMORY LIMITS
        # ====================================

        self.MAX_ARCHIVE_SIZE = 100

        self.MAX_HISTORY_SIZE = 250

        self.MAX_LINEAGE_SIZE = 50

        self.MAX_REASONING_HISTORY = 100

        self.MAX_EXECUTION_TRACE = 100

        # ====================================
        # CLEANUP HISTORY
        # ====================================

        self.cleanup_history = []

        self.cleaned_keys = []

        self.removed_strategies = 0

        self.removed_lineage = 0

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "garbage_collection":
            True,

            "lineage_pruning":
            True,

            "runtime_cleanup":
            True,

            "adaptive_memory_control":
            True,

            "context_stabilization":
            True
        }

    # ========================================
    # BUILD LIGHTWEIGHT SIGNATURE
    # ========================================

    def build_signature(

        self,

        value
    ):

        try:

            return {

                "type":
                type(value).__name__,

                "length":

                len(value)

                if hasattr(
                    value,
                    "__len__"
                )

                else 1,

                "id":
                id(value)
            }

        except Exception:

            return {

                "type":
                "unknown"
            }

    # ========================================
    # PRUNE STRATEGY ARCHIVE
    # ========================================

    def prune_strategy_archive(

        self,

        strategy_archive
    ):

        if not isinstance(
            strategy_archive,
            list
        ):

            return []

        # ====================================
        # SORT STRATEGIES
        # ====================================

        sorted_archive = sorted(

            strategy_archive,

            key=lambda strategy:

            (

                strategy.get(
                    "score",
                    0.0
                ),

                strategy.get(
                    "usage_count",
                    0
                )

            ),

            reverse=True
        )

        # ====================================
        # LIMIT SIZE
        # ====================================

        if len(sorted_archive) > (

            self.MAX_ARCHIVE_SIZE
        ):

            removed = (

                len(sorted_archive)

                -

                self.MAX_ARCHIVE_SIZE
            )

            self.removed_strategies += (
                removed
            )

            sorted_archive = sorted_archive[
                :self.MAX_ARCHIVE_SIZE
            ]

        return sorted_archive

    # ========================================
    # PRUNE LINEAGE HISTORY
    # ========================================

    def prune_lineage_history(

        self,

        lineage_history
    ):

        if not isinstance(
            lineage_history,
            list
        ):

            return []

        if len(lineage_history) > (

            self.MAX_LINEAGE_SIZE
        ):

            removed = (

                len(lineage_history)

                -

                self.MAX_LINEAGE_SIZE
            )

            self.removed_lineage += (
                removed
            )

            lineage_history = lineage_history[
                -self.MAX_LINEAGE_SIZE:
            ]

        return lineage_history

    # ========================================
    # CLEANUP RUNTIME CONTEXT
    # ========================================

    def cleanup_runtime_context(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            return {}

        # ====================================
        # HEAVY KEYS
        # ====================================

        heavy_keys = [

            "execution_trace",

            "recursive_report",

            "symbolic_report",

            "causal_report",

            "adaptive_execution_report",

            "merged_strategies",

            "orchestration_history",

            "old_reasoning_reports",

            "stale_synthesis",

            "governance_history"
        ]

        for key in heavy_keys:

            if key in runtime_context:

                runtime_context[key] = None

                self.cleaned_keys.append(
                    key
                )

        return runtime_context

    # ========================================
    # ENFORCE MEMORY LIMITS
    # ========================================

    def enforce_memory_limits(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            return {}

        # ====================================
        # STRATEGY ARCHIVE
        # ====================================

        if "strategy_archive" in (
            runtime_context
        ):

            runtime_context[
                "strategy_archive"
            ] = (

                self.prune_strategy_archive(

                    runtime_context.get(
                        "strategy_archive",
                        []
                    )
                )
            )

        # ====================================
        # LINEAGE HISTORY
        # ====================================

        if "lineage_history" in (
            runtime_context
        ):

            runtime_context[
                "lineage_history"
            ] = (

                self.prune_lineage_history(

                    runtime_context.get(
                        "lineage_history",
                        []
                    )
                )
            )

        return runtime_context

    # ========================================
    # BUILD CLEANUP REPORT
    # ========================================

    def build_cleanup_report(

        self,

        runtime_context
    ):

        memory_before = len(
            runtime_context
        )

        runtime_context = (

            self.cleanup_runtime_context(

                runtime_context
            )
        )

        runtime_context = (

            self.enforce_memory_limits(

                runtime_context
            )
        )

        memory_after = len(
            runtime_context
        )

        report = {

            "removed_strategies":
            self.removed_strategies,

            "removed_lineage":
            self.removed_lineage,

            "memory_pressure_before":
            memory_before,

            "memory_pressure_after":
            memory_after,

            "cleaned_context_keys":
            self.cleaned_keys,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.cleanup_history.append(
            report
        )

        # ====================================
        # FORCE GARBAGE COLLECTION
        # ====================================

        gc.collect()

        return report

    # ========================================
    # RUN CLEANUP CYCLE
    # ========================================

    def run_cleanup_cycle(

        self,

        runtime_context
    ):

        cleanup_report = (

            self.build_cleanup_report(

                runtime_context
            )
        )

        return {

            "runtime_context":
            runtime_context,

            "cleanup_report":
            cleanup_report
        }

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_cleanup = {}

        if self.cleanup_history:

            latest_cleanup = (

                self.cleanup_history[-1]
            )

        return {

            "cleanup_cycles":

            len(
                self.cleanup_history
            ),

            "removed_strategies":
            self.removed_strategies,

            "removed_lineage":
            self.removed_lineage,

            "engine_state":
            self.engine_state,

            "latest_cleanup":
            latest_cleanup
        }


# ============================================
# GLOBAL COLLECTOR
# ============================================

strategy_garbage_collector = (
    StrategyGarbageCollector()
)