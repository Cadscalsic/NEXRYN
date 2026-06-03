# ============================================
# NEXRYN RUNTIME STABILITY MANAGER
# ============================================

from datetime import datetime

import gc


# ============================================
# RUNTIME STABILITY MANAGER
# ============================================

class RuntimeStabilityManager:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # PRESSURE HISTORY
        # ====================================

        self.pressure_history = []

        # ====================================
        # STABILITY HISTORY
        # ====================================

        self.stability_history = []

        # ====================================
        # ACTIVE PROTECTIONS
        # ====================================

        self.active_protections = []

        # ====================================
        # THROTTLING HISTORY
        # ====================================

        self.throttling_history = []

        # ====================================
        # STABILIZATION EVENTS
        # ====================================

        self.stabilization_events = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "runtime_monitoring":
            True,

            "adaptive_throttling":
            True,

            "recursive_protection":
            True,

            "emergency_stabilization":
            True,

            "cognitive_pressure_tracking":
            True
        }

    # ========================================
    # MONITOR RUNTIME PRESSURE
    # ========================================

    def monitor_runtime_pressure(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        # ====================================
        # SAFE EXECUTION TRACE NORMALIZATION
        # ====================================

        execution_trace = runtime_context.get(
            "execution_trace",
            []
        )

        # ====================================
        # NONE NORMALIZATION
        # ====================================

        if execution_trace is None:

            execution_trace = []

        # ====================================
        # TYPE NORMALIZATION
        # ====================================

        if not isinstance(
            execution_trace,
            list
        ):

            execution_trace = []

        # ====================================
        # SAFE TRACE SIZE
        # ====================================

        execution_trace_size = len(
            execution_trace
        )        

        # ====================================
        # BASIC METRICS
        # ====================================

        context_size = len(
            runtime_context
        )

        recursive_depth = len(

            runtime_context.get(

                "recursive_paths",

                []
            )
        )

        lineage_count = len(

            runtime_context.get(

                "lineage_history",

                []
            )
        )



        reasoning_reports = 0

        # ====================================
        # REASONING REPORT COUNT
        # ====================================

        reasoning_keys = [

            "reasoning_report",

            "recursive_report",

            "symbolic_report",

            "causal_report",

            "analogical_report",

            "spatial_reasoning_report"
        ]

        for key in reasoning_keys:

            if key in runtime_context:

                reasoning_reports += 1

        # ====================================
        # PRESSURE SCORE
        # ====================================

        pressure_score = (

            context_size * 0.15

            +

            recursive_depth * 0.25

            +

            lineage_count * 0.20

            +

            execution_trace_size * 0.15

            +

            reasoning_reports * 0.25
        )

        pressure_report = {

            "context_size":
            context_size,

            "recursive_depth":
            recursive_depth,

            "lineage_count":
            lineage_count,

            "execution_trace_size":
            execution_trace_size,

            "reasoning_reports":
            reasoning_reports,

            "pressure_score":
            round(
                pressure_score,
                4
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.pressure_history.append(
            pressure_report
        )

        return pressure_report
    


    # ========================================
    # COMPUTE STABILITY SCORE
    # ========================================

    def compute_stability_score(

        self,

        pressure_report
    ):

        pressure_score = (

            pressure_report.get(
                "pressure_score",
                0.0
            )
        )

        if pressure_score < 10:

            stability_state = (
                "stable"
            )

        elif pressure_score < 25:

            stability_state = (
                "elevated"
            )

        elif pressure_score < 40:

            stability_state = (
                "degraded"
            )

        else:

            stability_state = (
                "critical"
            )

        stability_report = {

            "stability_state":
            stability_state,

            "pressure_score":
            pressure_score,

            "timestamp":
            str(datetime.utcnow())
        }

        self.stability_history.append(
            stability_report
        )

        return stability_report

    # ========================================
    # EMERGENCY STABILIZATION
    # ========================================

    def emergency_stabilization(

        self,

        runtime_context
    ):

        protections = []

        # ====================================
        # DISABLE RECURSIVE EXPANSION
        # ====================================

        runtime_context[
            "recursive_expansion_enabled"
        ] = False

        protections.append(
            "recursive_expansion_disabled"
        )

        # ====================================
        # REDUCE REASONING DEPTH
        # ====================================

        runtime_context[
            "max_reasoning_depth"
        ] = 2

        protections.append(
            "reasoning_depth_reduced"
        )

        # ====================================
        # DISABLE STRATEGY MERGING
        # ====================================

        runtime_context[
            "strategy_merging_enabled"
        ] = False

        protections.append(
            "strategy_merging_disabled"
        )

        # ====================================
        # CLEAN EXECUTION TRACE
        # ====================================

        if "execution_trace" in (
            runtime_context
        ):

            runtime_context[
                "execution_trace"
            ] = []

            protections.append(
                "execution_trace_cleaned"
            )

        # ====================================
        # FORCE GARBAGE COLLECTION
        # ====================================

        gc.collect()

        stabilization_report = {

            "stabilization":
            "emergency",

            "active_protections":
            protections,

            "timestamp":
            str(datetime.utcnow())
        }

        self.stabilization_events.append(
            stabilization_report
        )

        self.active_protections.extend(
            protections
        )

        return stabilization_report

    # ========================================
    # APPLY ADAPTIVE THROTTLING
    # ========================================

    def apply_adaptive_throttling(

        self,

        runtime_context,

        stability_state
    ):

        throttling_actions = []

        # ====================================
        # DEGRADED STATE
        # ====================================

        if stability_state == (

            "degraded"
        ):

            runtime_context[
                "mutation_rate"
            ] = 0.10

            throttling_actions.append(
                "mutation_rate_reduced"
            )

            runtime_context[
                "max_synthesis_cycles"
            ] = 2

            throttling_actions.append(
                "synthesis_cycles_reduced"
            )

        # ====================================
        # CRITICAL STATE
        # ====================================

        elif stability_state == (

            "critical"
        ):

            runtime_context[
                "mutation_rate"
            ] = 0.05

            throttling_actions.append(
                "critical_mutation_limit"
            )

            runtime_context[
                "max_synthesis_cycles"
            ] = 1

            throttling_actions.append(
                "critical_synthesis_limit"
            )

            runtime_context[
                "orchestration_depth"
            ] = 1

            throttling_actions.append(
                "orchestration_depth_reduced"
            )

        throttling_report = {

            "stability_state":
            stability_state,

            "throttling_actions":
            throttling_actions,

            "timestamp":
            str(datetime.utcnow())
        }

        self.throttling_history.append(
            throttling_report
        )

        return throttling_report

    # ========================================
    # BUILD STABILITY REPORT
    # ========================================

    def build_stability_report(

        self,

        pressure_report,

        stability_report
    ):

        return {

            "runtime_pressure":

            pressure_report.get(
                "pressure_score",
                0.0
            ),

            "recursive_pressure":

            pressure_report.get(
                "recursive_depth",
                0
            ),

            "memory_load":

            pressure_report.get(
                "context_size",
                0
            ),

            "lineage_pressure":

            pressure_report.get(
                "lineage_count",
                0
            ),

            "stability_state":

            stability_report.get(
                "stability_state",
                "stable"
            ),

            "active_protections":
            self.active_protections,

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN STABILITY CYCLE
    # ========================================

    def run_stability_cycle(

        self,

        runtime_context
    ):

        # ====================================
        # MONITOR PRESSURE
        # ====================================

        pressure_report = (

            self.monitor_runtime_pressure(

                runtime_context
            )
        )

        # ====================================
        # COMPUTE STABILITY
        # ====================================

        stability_report = (

            self.compute_stability_score(

                pressure_report
            )
        )

        stability_state = (

            stability_report.get(
                "stability_state"
            )
        )

        # ====================================
        # APPLY THROTTLING
        # ====================================

        throttling_report = (

            self.apply_adaptive_throttling(

                runtime_context,

                stability_state
            )
        )

        # ====================================
        # EMERGENCY MODE
        # ====================================

        emergency_report = {}

        if stability_state == (
            "critical"
        ):

            emergency_report = (

                self.emergency_stabilization(

                    runtime_context
                )
            )

        # ====================================
        # FINAL REPORT
        # ====================================

        final_report = (

            self.build_stability_report(

                pressure_report,

                stability_report
            )
        )

        return {

            "pressure_report":
            pressure_report,

            "stability_report":
            stability_report,

            "throttling_report":
            throttling_report,

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

        if self.stability_history:

            latest_report = (

                self.stability_history[-1]
            )

        return {

            "pressure_cycles":

            len(
                self.pressure_history
            ),

            "stability_cycles":

            len(
                self.stability_history
            ),

            "stabilization_events":

            len(
                self.stabilization_events
            ),

            "active_protections":
            self.active_protections,

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL STABILITY MANAGER
# ============================================

runtime_stability_manager = (
    RuntimeStabilityManager()
)