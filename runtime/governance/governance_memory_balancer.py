# ============================================
# NEXRYN GOVERNANCE MEMORY BALANCER
# ============================================

from datetime import datetime

import gc


# ============================================
# GOVERNANCE MEMORY BALANCER
# ============================================

class GovernanceMemoryBalancer:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # MEMORY LIMITS
        # ====================================

        self.MAX_GOVERNANCE_HISTORY = 250

        self.MAX_STRATEGY_ARCHIVE = 100

        self.MAX_LINEAGE_HISTORY = 50

        self.MAX_REASONING_MEMORY = 100

        self.MAX_EXECUTION_TRACE = 100

        # ====================================
        # BALANCING HISTORY
        # ====================================

        self.balance_history = []

        self.rebalanced_sections = []

        self.protected_cognition_zones = []

        self.detected_imbalances = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "memory_balancing":
            True,

            "adaptive_allocation":
            True,

            "governance_stabilization":
            True,

            "cognitive_memory_protection":
            True,

            "runtime_memory_optimization":
            True
        }

    # ========================================
    # SAFE COLLECTION SIZE
    # ========================================

    def safe_collection_size(

        self,

        runtime_context,

        key
    ):

        value = runtime_context.get(
            key,
            []
        )

        if value is None:

            value = []

        if not isinstance(

            value,

            (
                list,
                dict,
                tuple,
                set
            )
        ):

            value = []

        return len(value)

    # ========================================
    # ANALYZE MEMORY DISTRIBUTION
    # ========================================

    def analyze_memory_distribution(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        # ====================================
        # SAFE MEMORY SIZES
        # ====================================

        governance_history_size = (

            self.safe_collection_size(

                runtime_context,

                "governance_history"
            )
        )

        strategy_archive_size = (

            self.safe_collection_size(

                runtime_context,

                "strategy_archive"
            )
        )

        lineage_memory_size = (

            self.safe_collection_size(

                runtime_context,

                "lineage_history"
            )
        )

        reasoning_memory_size = (

            self.safe_collection_size(

                runtime_context,

                "reasoning_history"
            )
        )

        execution_memory_size = (

            self.safe_collection_size(

                runtime_context,

                "execution_trace"
            )
        )

        # ====================================
        # BUILD DISTRIBUTION
        # ====================================

        distribution = {

            "governance_history_size":
            governance_history_size,

            "strategy_archive_size":
            strategy_archive_size,

            "lineage_memory_size":
            lineage_memory_size,

            "reasoning_memory_size":
            reasoning_memory_size,

            "execution_memory_size":
            execution_memory_size,

            "runtime_context_size":
            len(runtime_context),

            "timestamp":
            str(datetime.utcnow())
        }

        return distribution

    # ========================================
    # DETECT MEMORY IMBALANCE
    # ========================================

    def detect_memory_imbalance(

        self,

        distribution
    ):

        imbalance_level = "stable"

        imbalance_sources = []

        # ====================================
        # GOVERNANCE HISTORY
        # ====================================

        if (

            distribution[
                "governance_history_size"
            ]

            >

            self.MAX_GOVERNANCE_HISTORY
        ):

            imbalance_level = "elevated"

            imbalance_sources.append(
                "governance_history_overload"
            )

        # ====================================
        # STRATEGY ARCHIVE
        # ====================================

        if (

            distribution[
                "strategy_archive_size"
            ]

            >

            self.MAX_STRATEGY_ARCHIVE
        ):

            imbalance_level = "degraded"

            imbalance_sources.append(
                "strategy_archive_overload"
            )

        # ====================================
        # LINEAGE MEMORY
        # ====================================

        if (

            distribution[
                "lineage_memory_size"
            ]

            >

            self.MAX_LINEAGE_HISTORY
        ):

            imbalance_level = "critical"

            imbalance_sources.append(
                "recursive_lineage_pressure"
            )

        # ====================================
        # EXECUTION TRACE
        # ====================================

        if (

            distribution[
                "execution_memory_size"
            ]

            >

            self.MAX_EXECUTION_TRACE
        ):

            imbalance_sources.append(
                "execution_trace_overload"
            )

        imbalance_report = {

            "imbalance_level":
            imbalance_level,

            "imbalance_sources":
            imbalance_sources,

            "timestamp":
            str(datetime.utcnow())
        }

        self.detected_imbalances.append(
            imbalance_report
        )

        return imbalance_report

    # ========================================
    # REBALANCE MEMORY
    # ========================================

    def rebalance_memory(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        rebalanced_sections = []

        # ====================================
        # GOVERNANCE HISTORY
        # ====================================

        history = runtime_context.get(
            "governance_history",
            []
        )

        if isinstance(history, list):

            if len(history) > (

                self.MAX_GOVERNANCE_HISTORY
            ):

                runtime_context[
                    "governance_history"
                ] = history[
                    -self.MAX_GOVERNANCE_HISTORY:
                ]

                rebalanced_sections.append(
                    "governance_history"
                )

        # ====================================
        # STRATEGY ARCHIVE
        # ====================================

        archive = runtime_context.get(
            "strategy_archive",
            []
        )

        if isinstance(archive, list):

            if len(archive) > (

                self.MAX_STRATEGY_ARCHIVE
            ):

                runtime_context[
                    "strategy_archive"
                ] = archive[
                    -self.MAX_STRATEGY_ARCHIVE:
                ]

                rebalanced_sections.append(
                    "strategy_archive"
                )

        # ====================================
        # LINEAGE HISTORY
        # ====================================

        lineage = runtime_context.get(
            "lineage_history",
            []
        )

        if isinstance(lineage, list):

            if len(lineage) > (

                self.MAX_LINEAGE_HISTORY
            ):

                runtime_context[
                    "lineage_history"
                ] = lineage[
                    -self.MAX_LINEAGE_HISTORY:
                ]

                rebalanced_sections.append(
                    "lineage_history"
                )

        # ====================================
        # EXECUTION TRACE
        # ====================================

        execution_trace = runtime_context.get(
            "execution_trace",
            []
        )

        if execution_trace is None:

            execution_trace = []

        if isinstance(execution_trace, list):

            if len(execution_trace) > (

                self.MAX_EXECUTION_TRACE
            ):

                runtime_context[
                    "execution_trace"
                ] = execution_trace[
                    -self.MAX_EXECUTION_TRACE:
                ]

                rebalanced_sections.append(
                    "execution_trace"
                )

        self.rebalanced_sections.extend(
            rebalanced_sections
        )

        return runtime_context

    # ========================================
    # APPLY ADAPTIVE ALLOCATION
    # ========================================

    def apply_adaptive_allocation(

        self,

        runtime_context
    ):

        protected_zones = []

        active_zones = [

            "current_reasoning",

            "active_hypotheses",

            "adaptive_execution",

            "runtime_state"
        ]

        for zone in active_zones:

            if zone in runtime_context:

                protected_zones.append(
                    zone
                )

        self.protected_cognition_zones = (
            protected_zones
        )

        allocation_report = {

            "protected_cognition_zones":
            protected_zones,

            "allocation_mode":
            "adaptive_priority",

            "timestamp":
            str(datetime.utcnow())
        }

        return allocation_report

    # ========================================
    # BUILD BALANCE REPORT
    # ========================================

    def build_balance_report(

        self,

        distribution,

        imbalance_report
    ):

        memory_pressure = (

            distribution.get(
                "runtime_context_size",
                0
            )
        )

        return {

            "memory_distribution":
            distribution,

            "imbalance_level":

            imbalance_report.get(
                "imbalance_level",
                "stable"
            ),

            "imbalance_sources":

            imbalance_report.get(
                "imbalance_sources",
                []
            ),

            "rebalanced_sections":
            self.rebalanced_sections,

            "protected_cognition_zones":
            self.protected_cognition_zones,

            "memory_pressure":
            memory_pressure,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN BALANCING CYCLE
    # ========================================

    def run_balancing_cycle(

        self,

        runtime_context
    ):

        distribution = (

            self.analyze_memory_distribution(

                runtime_context
            )
        )

        imbalance_report = (

            self.detect_memory_imbalance(

                distribution
            )
        )

        runtime_context = (

            self.rebalance_memory(

                runtime_context
            )
        )

        allocation_report = (

            self.apply_adaptive_allocation(

                runtime_context
            )
        )

        balance_report = (

            self.build_balance_report(

                distribution,

                imbalance_report
            )
        )

        self.balance_history.append(
            balance_report
        )

        gc.collect()

        return {

            "runtime_context":
            runtime_context,

            "allocation_report":
            allocation_report,

            "balance_report":
            balance_report
        }

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_balance = {}

        if self.balance_history:

            latest_balance = (

                self.balance_history[-1]
            )

        return {

            "balance_cycles":

            len(
                self.balance_history
            ),

            "detected_imbalances":

            len(
                self.detected_imbalances
            ),

            "rebalanced_sections":
            self.rebalanced_sections,

            "protected_cognition_zones":
            self.protected_cognition_zones,

            "engine_state":
            self.engine_state,

            "latest_balance":
            latest_balance
        }


# ============================================
# GLOBAL MEMORY BALANCER
# ============================================

governance_memory_balancer = (
    GovernanceMemoryBalancer()
)