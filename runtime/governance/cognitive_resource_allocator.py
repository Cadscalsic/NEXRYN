# ============================================
# NEXRYN COGNITIVE RESOURCE ALLOCATOR
# ============================================

from datetime import datetime

import gc


# ============================================
# COGNITIVE RESOURCE ALLOCATOR
# ============================================

class CognitiveResourceAllocator:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # RESOURCE HISTORY
        # ====================================

        self.resource_history = []

        self.allocation_history = []

        self.emergency_history = []

        self.priority_history = []

        self.protected_systems = []

        self.throttled_systems = []

        # ====================================
        # RESOURCE LIMITS
        # ====================================

        self.MAX_REASONING_BUDGET = 5

        self.MAX_SYNTHESIS_CYCLES = 3

        self.MAX_ORCHESTRATION_DEPTH = 3

        self.MAX_MUTATION_RATE = 0.25

        self.MAX_RECURSION_PRESSURE = 10

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "adaptive_resource_allocation":
            True,

            "cognitive_load_monitoring":
            True,

            "emergency_resource_control":
            True,

            "runtime_resource_balancing":
            True,

            "recursive_pressure_management":
            True,

            "governance_stabilization":
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
    # ANALYZE COGNITIVE LOAD
    # ========================================

    def analyze_cognitive_load(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        # ====================================
        # SAFE LOAD ANALYSIS
        # ====================================

        reasoning_load = (

            self.safe_collection_size(

                runtime_context,

                "reasoning_history"
            )
        )

        synthesis_load = (

            self.safe_collection_size(

                runtime_context,

                "synthesis_history"
            )
        )

        governance_pressure = (

            self.safe_collection_size(

                runtime_context,

                "governance_history"
            )
        )

        recursion_pressure = (

            self.safe_collection_size(

                runtime_context,

                "recursive_paths"
            )
        )

        execution_pressure = (

            self.safe_collection_size(

                runtime_context,

                "execution_trace"
            )
        )

        lineage_pressure = (

            self.safe_collection_size(

                runtime_context,

                "lineage_history"
            )
        )

        memory_pressure = len(
            runtime_context
        )

        # ====================================
        # COMPUTE TOTAL LOAD
        # ====================================

        total_load = (

            reasoning_load * 0.20

            +

            synthesis_load * 0.15

            +

            governance_pressure * 0.15

            +

            recursion_pressure * 0.20

            +

            execution_pressure * 0.10

            +

            lineage_pressure * 0.10

            +

            memory_pressure * 0.10
        )

        load_state = "stable"

        if total_load >= 20:

            load_state = "elevated"

        if total_load >= 35:

            load_state = "degraded"

        if total_load >= 50:

            load_state = "critical"

        load_report = {

            "reasoning_load":
            reasoning_load,

            "synthesis_load":
            synthesis_load,

            "governance_pressure":
            governance_pressure,

            "recursion_pressure":
            recursion_pressure,

            "execution_pressure":
            execution_pressure,

            "lineage_pressure":
            lineage_pressure,

            "memory_pressure":
            memory_pressure,

            "total_load":
            round(
                total_load,
                4
            ),

            "load_state":
            load_state,

            "timestamp":
            str(datetime.utcnow())
        }

        self.resource_history.append(
            load_report
        )

        return load_report

    # ========================================
    # PRIORITIZE RESOURCES
    # ========================================

    def prioritize_cognitive_resources(

        self,

        runtime_context
    ):

        priority_map = {

            "active_reasoning":
            "critical",

            "current_task_execution":
            "critical",

            "adaptive_stabilization":
            "high",

            "governance_runtime":
            "high",

            "recursive_expansion":
            "restricted",

            "strategy_merging":
            "restricted",

            "old_archives":
            "low",

            "stale_lineage":
            "low"
        }

        self.protected_systems = [

            "active_reasoning",

            "current_task_execution",

            "adaptive_stabilization",

            "governance_runtime"
        ]

        self.throttled_systems = [

            "recursive_expansion",

            "strategy_merging",

            "old_archives",

            "stale_lineage"
        ]

        priority_report = {

            "priority_map":
            priority_map,

            "protected_systems":
            self.protected_systems,

            "throttled_systems":
            self.throttled_systems,

            "timestamp":
            str(datetime.utcnow())
        }

        self.priority_history.append(
            priority_report
        )

        return priority_report

    # ========================================
    # ALLOCATE RESOURCES
    # ========================================

    def allocate_resources(

        self,

        runtime_context,

        load_report
    ):

        total_load = load_report.get(
            "total_load",
            0.0
        )

        allocation = {

            "reasoning_budget":
            self.MAX_REASONING_BUDGET,

            "synthesis_cycles":
            self.MAX_SYNTHESIS_CYCLES,

            "orchestration_depth":
            self.MAX_ORCHESTRATION_DEPTH,

            "mutation_rate":
            self.MAX_MUTATION_RATE
        }

        # ====================================
        # ELEVATED LOAD
        # ====================================

        if total_load >= 20:

            allocation[
                "synthesis_cycles"
            ] = 2

            allocation[
                "mutation_rate"
            ] = 0.15

        # ====================================
        # DEGRADED LOAD
        # ====================================

        if total_load >= 35:

            allocation[
                "reasoning_budget"
            ] = 3

            allocation[
                "orchestration_depth"
            ] = 2

            allocation[
                "mutation_rate"
            ] = 0.10

        # ====================================
        # CRITICAL LOAD
        # ====================================

        if total_load >= 50:

            allocation[
                "reasoning_budget"
            ] = 1

            allocation[
                "synthesis_cycles"
            ] = 1

            allocation[
                "orchestration_depth"
            ] = 1

            allocation[
                "mutation_rate"
            ] = 0.05

        # ====================================
        # APPLY ALLOCATION
        # ====================================

        runtime_context[
            "reasoning_budget"
        ] = allocation[
            "reasoning_budget"
        ]

        runtime_context[
            "max_synthesis_cycles"
        ] = allocation[
            "synthesis_cycles"
        ]

        runtime_context[
            "orchestration_depth"
        ] = allocation[
            "orchestration_depth"
        ]

        runtime_context[
            "mutation_rate"
        ] = allocation[
            "mutation_rate"
        ]

        allocation_report = {

            "allocation":
            allocation,

            "timestamp":
            str(datetime.utcnow())
        }

        self.allocation_history.append(
            allocation_report
        )

        return allocation_report

    # ========================================
    # EMERGENCY RESOURCE REALLOCATION
    # ========================================

    def emergency_resource_reallocation(

        self,

        runtime_context,

        load_report
    ):

        total_load = load_report.get(
            "total_load",
            0.0
        )

        emergency_state = False

        emergency_actions = []

        # ====================================
        # CRITICAL LOAD PROTECTION
        # ====================================

        if total_load >= 50:

            emergency_state = True

            runtime_context[
                "safe_mode"
            ] = True

            emergency_actions.append(
                "safe_mode_enabled"
            )

            runtime_context[
                "recursive_expansion_enabled"
            ] = False

            emergency_actions.append(
                "recursive_expansion_disabled"
            )

            runtime_context[
                "strategy_merging_enabled"
            ] = False

            emergency_actions.append(
                "strategy_merging_disabled"
            )

            runtime_context[
                "advanced_synthesis_enabled"
            ] = False

            emergency_actions.append(
                "advanced_synthesis_disabled"
            )

            runtime_context[
                "recursive_governance_enabled"
            ] = False

            emergency_actions.append(
                "recursive_governance_disabled"
            )

            # ================================
            # SAFE EXECUTION TRACE CLEANUP
            # ================================

            if "execution_trace" in (
                runtime_context
            ):

                runtime_context[
                    "execution_trace"
                ] = []

                emergency_actions.append(
                    "execution_trace_cleaned"
                )

            gc.collect()

        emergency_report = {

            "emergency_state":
            emergency_state,

            "emergency_actions":
            emergency_actions,

            "timestamp":
            str(datetime.utcnow())
        }

        self.emergency_history.append(
            emergency_report
        )

        return emergency_report

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_allocation_report(

        self,

        load_report,

        allocation_report,

        emergency_report
    ):

        return {

            "cognitive_load":
            load_report,

            "allocated_resources":

            allocation_report.get(
                "allocation",
                {}
            ),

            "protected_systems":
            self.protected_systems,

            "throttled_systems":
            self.throttled_systems,

            "emergency_state":

            emergency_report.get(
                "emergency_state",
                False
            ),

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN RESOURCE ALLOCATION CYCLE
    # ========================================

    def run_resource_allocation_cycle(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        # ====================================
        # ANALYZE LOAD
        # ====================================

        load_report = (

            self.analyze_cognitive_load(

                runtime_context
            )
        )

        # ====================================
        # PRIORITIZE RESOURCES
        # ====================================

        priority_report = (

            self.prioritize_cognitive_resources(

                runtime_context
            )
        )

        # ====================================
        # ALLOCATE RESOURCES
        # ====================================

        allocation_report = (

            self.allocate_resources(

                runtime_context,

                load_report
            )
        )

        # ====================================
        # EMERGENCY PROTECTION
        # ====================================

        emergency_report = (

            self.emergency_resource_reallocation(

                runtime_context,

                load_report
            )
        )

        # ====================================
        # BUILD FINAL REPORT
        # ====================================

        final_report = (

            self.build_allocation_report(

                load_report,

                allocation_report,

                emergency_report
            )
        )

        return {

            "priority_report":
            priority_report,

            "allocation_report":
            allocation_report,

            "emergency_report":
            emergency_report,

            "final_report":
            final_report
        }

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.allocation_history:

            latest_report = (

                self.allocation_history[-1]
            )

        return {

            "resource_cycles":

            len(
                self.resource_history
            ),

            "allocation_cycles":

            len(
                self.allocation_history
            ),

            "priority_cycles":

            len(
                self.priority_history
            ),

            "emergency_cycles":

            len(
                self.emergency_history
            ),

            "protected_systems":
            self.protected_systems,

            "throttled_systems":
            self.throttled_systems,

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL RESOURCE ALLOCATOR
# ============================================

cognitive_resource_allocator = (
    CognitiveResourceAllocator()
)