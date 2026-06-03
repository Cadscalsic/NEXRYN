# ============================================
# NEXRYN RECURSIVE DEPTH REGULATOR
# ============================================

from datetime import datetime


# ============================================
# RECURSIVE DEPTH REGULATOR
# ============================================

class RecursiveDepthRegulator:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # REGULATION STATE
        # ====================================

        self.regulation_state = {

            "recursive_regulation":
            True,

            "depth_stabilization":
            True,

            "recursive_pruning":
            True,

            "adaptive_recursion":
            True,

            "loop_prevention":
            True,

            "regulation_cycles":
            0
        }

        # ====================================
        # DEPTH HISTORY
        # ====================================

        self.depth_history = []

    # ========================================
    # ANALYZE RECURSION
    # ========================================

    def analyze_recursion(

        self,

        runtime_context
    ):

        inference_report = (

            runtime_context.get(
                "inference_report"
            )

            or {}
        )

        recursive_report = (

            runtime_context.get(
                "recursive_report"
            )

            or {}
        )

        reasoning_depth = (

            inference_report.get(
                "reasoning_depth",
                0
            )
        )

        hypothesis_count = (

            recursive_report.get(
                "hypothesis_count",
                0
            )
        )

        hierarchy_levels = (

            recursive_report.get(
                "hierarchy_levels",
                {}
            )
        )

        return {

            "reasoning_depth":
            reasoning_depth,

            "hypothesis_count":
            hypothesis_count,

            "hierarchy_levels":
            hierarchy_levels,

            "recursive_state":
            self.classify_recursive_state(

                reasoning_depth,

                hypothesis_count
            )
        }

    # ========================================
    # CLASSIFY RECURSIVE STATE
    # ========================================

    def classify_recursive_state(

        self,

        reasoning_depth,

        hypothesis_count
    ):

        if (

            reasoning_depth >= 25
            or hypothesis_count >= 15
        ):

            return "critical"

        if (

            reasoning_depth >= 18
            or hypothesis_count >= 10
        ):

            return "high"

        if (

            reasoning_depth >= 10
            or hypothesis_count >= 5
        ):

            return "moderate"

        return "stable"

    # ========================================
    # BUILD REGULATION ACTIONS
    # ========================================

    def build_regulation_actions(

        self,

        recursive_report
    ):

        actions = []

        recursive_state = (

            recursive_report.get(
                "recursive_state"
            )
        )

        # ====================================
        # CRITICAL RECURSION
        # ====================================

        if recursive_state == "critical":

            actions.extend([

                {

                    "action":
                    "hard_limit_recursive_expansion",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "prune_recursive_branches",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "activate_emergency_compression",

                    "priority":
                    "critical"
                }
            ])

        # ====================================
        # HIGH RECURSION
        # ====================================

        elif recursive_state == "high":

            actions.extend([

                {

                    "action":
                    "reduce_reasoning_depth",

                    "priority":
                    "high"
                },

                {

                    "action":
                    "limit_hypothesis_branching",

                    "priority":
                    "high"
                }
            ])

        # ====================================
        # MODERATE RECURSION
        # ====================================

        elif recursive_state == "moderate":

            actions.append({

                "action":
                "maintain_balanced_recursion",

                "priority":
                "medium"
            })

        # ====================================
        # STABLE RECURSION
        # ====================================

        else:

            actions.append({

                "action":
                "allow_recursive_exploration",

                "priority":
                "low"
            })

        return actions

    # ========================================
    # RUN REGULATION CYCLE
    # ========================================

    def run_regulation_cycle(

        self,

        runtime_context
    ):

        recursive_report = (

            self.analyze_recursion(
                runtime_context
            )
        )

        regulation_actions = (

            self.build_regulation_actions(
                recursive_report
            )
        )

        regulation_report = {

            "recursive_analysis":
            recursive_report,

            "regulation_actions":
            regulation_actions,

            "timestamp":
            str(datetime.utcnow())
        }

        runtime_context[
            "recursive_regulation_report"
        ] = regulation_report

        self.depth_history.append(
            regulation_report
        )

        self.regulation_state[
            "regulation_cycles"
        ] += 1

        return runtime_context

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "regulation_cycles":
            self.regulation_state[
                "regulation_cycles"
            ],

            "depth_history":
            len(
                self.depth_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL RECURSIVE REGULATOR
# ============================================

recursive_depth_regulator = (
    RecursiveDepthRegulator()
)