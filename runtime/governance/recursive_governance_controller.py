# ============================================
# NEXRYN RECURSIVE GOVERNANCE CONTROLLER
# ============================================

from datetime import datetime

import gc


# ============================================
# RECURSIVE GOVERNANCE CONTROLLER
# ============================================

class RecursiveGovernanceController:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # RECURSION LIMITS
        # ====================================

        self.MAX_GOVERNANCE_DEPTH = 3

        self.MAX_REASONING_DEPTH = 5

        self.MAX_LINEAGE_DEPTH = 3

        self.MAX_EXECUTION_DEPTH = 3

        self.MAX_RECURSIVE_RISK = 4

        # ====================================
        # RECURSION HISTORY
        # ====================================

        self.recursive_history = []

        self.recursive_events = []

        self.recursive_protections = []

        self.instability_history = []

        self.safe_mode_history = []

        # ====================================
        # ENGINE STATE
        # ====================================

        self.engine_state = {

            "recursive_governance":
            True,

            "recursive_protection":
            True,

            "recursive_stabilization":
            True,

            "adaptive_recursion_control":
            True,

            "safe_recursive_execution":
            True
        }

    # ========================================
    # MONITOR RECURSIVE DEPTH
    # ========================================

    def monitor_recursive_depth(

        self,

        runtime_context
    ):

        if not isinstance(
            runtime_context,
            dict
        ):

            runtime_context = {}

        governance_depth = len(

            runtime_context.get(

                "governance_history",

                []
            )
        )

        reasoning_depth = len(

            runtime_context.get(

                "reasoning_history",

                []
            )
        )

        lineage_depth = len(

            runtime_context.get(

                "lineage_history",

                []
            )
        )

        execution_depth = len(

            runtime_context.get(

                "execution_trace",

                []
            )
        )

        recursive_depth_report = {

            "governance_depth":
            governance_depth,

            "reasoning_depth":
            reasoning_depth,

            "lineage_depth":
            lineage_depth,

            "execution_depth":
            execution_depth,

            "timestamp":
            str(datetime.utcnow())
        }

        self.recursive_history.append(
            recursive_depth_report
        )

        return recursive_depth_report

    # ========================================
    # DETECT RECURSIVE INSTABILITY
    # ========================================

    def detect_recursive_instability(

        self,

        recursive_depth_report
    ):

        recursive_risk = 0

        instability_sources = []

        # ====================================
        # GOVERNANCE DEPTH
        # ====================================

        if (

            recursive_depth_report[
                "governance_depth"
            ]

            >

            self.MAX_GOVERNANCE_DEPTH
        ):

            recursive_risk += 1

            instability_sources.append(
                "governance_depth_overflow"
            )

        # ====================================
        # REASONING DEPTH
        # ====================================

        if (

            recursive_depth_report[
                "reasoning_depth"
            ]

            >

            self.MAX_REASONING_DEPTH
        ):

            recursive_risk += 1

            instability_sources.append(
                "reasoning_depth_overflow"
            )

        # ====================================
        # LINEAGE DEPTH
        # ====================================

        if (

            recursive_depth_report[
                "lineage_depth"
            ]

            >

            self.MAX_LINEAGE_DEPTH
        ):

            recursive_risk += 1

            instability_sources.append(
                "lineage_depth_overflow"
            )

        # ====================================
        # EXECUTION DEPTH
        # ====================================

        if (

            recursive_depth_report[
                "execution_depth"
            ]

            >

            self.MAX_EXECUTION_DEPTH
        ):

            recursive_risk += 1

            instability_sources.append(
                "execution_depth_overflow"
            )

        instability_report = {

            "recursive_risk":
            recursive_risk,

            "instability_sources":
            instability_sources,

            "recursive_instability":

            recursive_risk >= (
                self.MAX_RECURSIVE_RISK
            ),

            "timestamp":
            str(datetime.utcnow())
        }

        self.instability_history.append(
            instability_report
        )

        return instability_report

    # ========================================
    # ENFORCE RECURSIVE LIMITS
    # ========================================

    def enforce_recursive_limits(

        self,

        runtime_context
    ):

        protections = []

        # ====================================
        # LIMIT REASONING DEPTH
        # ====================================

        runtime_context[
            "max_reasoning_depth"
        ] = min(

            runtime_context.get(
                "max_reasoning_depth",
                5
            ),

            self.MAX_REASONING_DEPTH
        )

        protections.append(
            "reasoning_depth_limited"
        )

        # ====================================
        # LIMIT ORCHESTRATION DEPTH
        # ====================================

        runtime_context[
            "orchestration_depth"
        ] = min(

            runtime_context.get(
                "orchestration_depth",
                3
            ),

            self.MAX_EXECUTION_DEPTH
        )

        protections.append(
            "orchestration_depth_limited"
        )

        # ====================================
        # DISABLE ADVANCED RECURSION
        # ====================================

        runtime_context[
            "advanced_recursive_expansion"
        ] = False

        protections.append(
            "advanced_recursion_disabled"
        )

        # ====================================
        # LIMIT SYNTHESIS
        # ====================================

        runtime_context[
            "recursive_synthesis_enabled"
        ] = False

        protections.append(
            "recursive_synthesis_disabled"
        )

        self.recursive_protections.extend(
            protections
        )

        return {

            "protections":
            protections,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # ACTIVATE RECURSIVE SAFE MODE
    # ========================================

    def activate_recursive_safe_mode(

        self,

        runtime_context
    ):

        runtime_context[
            "recursive_safe_mode"
        ] = True

        runtime_context[
            "advanced_recursive_expansion"
        ] = False

        runtime_context[
            "recursive_governance_enabled"
        ] = False

        runtime_context[
            "minimal_cognition_mode"
        ] = True

        runtime_context[
            "cognitive_branching_enabled"
        ] = False

        # ====================================
        # CLEAN HEAVY RECURSIVE STRUCTURES
        # ====================================

        recursive_keys = [

            "recursive_report",

            "recursive_paths",

            "recursive_history",

            "recursive_lineage",

            "recursive_execution_trace"
        ]

        cleaned_keys = []

        for key in recursive_keys:

            if key in runtime_context:

                runtime_context[key] = []

                cleaned_keys.append(
                    key
                )

        gc.collect()

        safe_mode_report = {

            "recursive_safe_mode":
            True,

            "cleaned_recursive_keys":
            cleaned_keys,

            "timestamp":
            str(datetime.utcnow())
        }

        self.safe_mode_history.append(
            safe_mode_report
        )

        return safe_mode_report

    # ========================================
    # BUILD RECURSIVE GOVERNANCE REPORT
    # ========================================

    def build_recursive_governance_report(

        self,

        recursive_depth_report,

        instability_report
    ):

        return {

            "recursive_depth":
            recursive_depth_report,

            "recursive_instability_level":

            instability_report.get(
                "recursive_risk",
                0
            ),

            "instability_sources":

            instability_report.get(
                "instability_sources",
                []
            ),

            "active_recursive_protections":
            self.recursive_protections,

            "recursive_safe_mode":

            len(
                self.safe_mode_history
            ) > 0,

            "governance_stabilization_state":

            "stable"

            if not instability_report.get(
                "recursive_instability",
                False
            )

            else "critical",

            "engine_state":
            self.engine_state,

            "timestamp":
            str(datetime.utcnow())
        }

    # ========================================
    # RUN RECURSIVE GOVERNANCE CYCLE
    # ========================================

    def run_recursive_governance_cycle(

        self,

        runtime_context
    ):

        # ====================================
        # MONITOR DEPTH
        # ====================================

        recursive_depth_report = (

            self.monitor_recursive_depth(

                runtime_context
            )
        )

        # ====================================
        # DETECT INSTABILITY
        # ====================================

        instability_report = (

            self.detect_recursive_instability(

                recursive_depth_report
            )
        )

        # ====================================
        # ENFORCE LIMITS
        # ====================================

        protection_report = (

            self.enforce_recursive_limits(

                runtime_context
            )
        )

        # ====================================
        # SAFE MODE
        # ====================================

        safe_mode_report = {}

        if instability_report.get(
            "recursive_instability",
            False
        ):

            safe_mode_report = (

                self.activate_recursive_safe_mode(

                    runtime_context
                )
            )

        # ====================================
        # BUILD FINAL REPORT
        # ====================================

        final_report = (

            self.build_recursive_governance_report(

                recursive_depth_report,

                instability_report
            )
        )

        recursive_cycle_report = {

            "recursive_depth_report":
            recursive_depth_report,

            "instability_report":
            instability_report,

            "protection_report":
            protection_report,

            "safe_mode_report":
            safe_mode_report,

            "final_report":
            final_report
        }

        self.recursive_events.append(
            recursive_cycle_report
        )

        return recursive_cycle_report

    # ========================================
    # BUILD SUMMARY
    # ========================================

    def build_summary(self):

        latest_report = {}

        if self.recursive_events:

            latest_report = (

                self.recursive_events[-1]
            )

        return {

            "recursive_cycles":

            len(
                self.recursive_events
            ),

            "instability_events":

            len(
                self.instability_history
            ),

            "safe_mode_activations":

            len(
                self.safe_mode_history
            ),

            "active_recursive_protections":
            self.recursive_protections,

            "engine_state":
            self.engine_state,

            "latest_report":
            latest_report
        }


# ============================================
# GLOBAL RECURSIVE CONTROLLER
# ============================================

recursive_governance_controller = (
    RecursiveGovernanceController()
)