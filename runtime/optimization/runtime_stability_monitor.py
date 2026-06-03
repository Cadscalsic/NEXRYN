# ============================================
# NEXRYN RUNTIME STABILITY MONITOR
# ============================================

from datetime import datetime


# ============================================
# RUNTIME STABILITY MONITOR
# ============================================

class RuntimeStabilityMonitor:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # STABILITY STATE
        # ====================================

        self.stability_state = {

            "runtime_stability":
            True,

            "recursive_stabilization":
            True,

            "semantic_alignment":
            True,

            "planning_stability":
            True,

            "cognitive_homeostasis":
            True,

            "stability_cycles":
            0
        }

        # ====================================
        # STABILITY HISTORY
        # ====================================

        self.stability_history = []

    # ========================================
    # ANALYZE STABILITY
    # ========================================

    def analyze_stability(

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

        evaluation_result = (

            runtime_context.get(
                "evaluation_result"
            )

            or {}
        )

        reasoning_depth = (

            inference_report.get(
                "reasoning_depth",
                0
            )
        )

        cognitive_pressure = (

            inference_report.get(
                "cognitive_pressure",
                0.0
            )
        )

        mutation_detected = (

            recursive_report.get(
                "mutation_detected",
                False
            )
        )

        accuracy = (

            evaluation_result.get(
                "accuracy",
                0.0
            )
        )

        context_size = len(
            runtime_context
        )

        stability_score = (

            accuracy * 0.4
            + (1 - cognitive_pressure) * 0.3
            + min(reasoning_depth / 20, 1.0) * 0.1
            + (0.2 if not mutation_detected else 0.1)
        )

        return {

            "reasoning_depth":
            reasoning_depth,

            "cognitive_pressure":
            cognitive_pressure,

            "mutation_detected":
            mutation_detected,

            "accuracy":
            accuracy,

            "context_size":
            context_size,

            "stability_score":
            round(
                stability_score,
                4
            ),

            "stability_state":
            self.classify_stability_state(
                stability_score
            )
        }

    # ========================================
    # CLASSIFY STABILITY
    # ========================================

    def classify_stability_state(

        self,

        stability_score
    ):

        if stability_score >= 0.85:

            return "stable"

        if stability_score >= 0.65:

            return "moderate"

        if stability_score >= 0.45:

            return "unstable"

        return "critical"

    # ========================================
    # BUILD STABILITY ACTIONS
    # ========================================

    def build_stability_actions(

        self,

        stability_report
    ):

        actions = []

        stability_state = (

            stability_report.get(
                "stability_state"
            )
        )

        # ====================================
        # CRITICAL STABILITY
        # ====================================

        if stability_state == "critical":

            actions.extend([

                {

                    "action":
                    "activate_runtime_recovery",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "reduce_recursive_cognition",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "freeze_semantic_mutation",

                    "priority":
                    "critical"
                }
            ])

        # ====================================
        # UNSTABLE STATE
        # ====================================

        elif stability_state == "unstable":

            actions.extend([

                {

                    "action":
                    "stabilize_reasoning_routes",

                    "priority":
                    "high"
                },

                {

                    "action":
                    "limit_exploration_intensity",

                    "priority":
                    "medium"
                }
            ])

        # ====================================
        # MODERATE STABILITY
        # ====================================

        elif stability_state == "moderate":

            actions.append({

                "action":
                "maintain_cognitive_balance",

                "priority":
                "medium"
            })

        # ====================================
        # STABLE STATE
        # ====================================

        else:

            actions.append({

                "action":
                "allow_adaptive_growth",

                "priority":
                "low"
            })

        return actions

    # ========================================
    # RUN STABILITY CYCLE
    # ========================================

    def run_stability_cycle(

        self,

        runtime_context
    ):

        stability_report = (

            self.analyze_stability(
                runtime_context
            )
        )

        stability_actions = (

            self.build_stability_actions(
                stability_report
            )
        )

        final_report = {

            "stability_analysis":
            stability_report,

            "stability_actions":
            stability_actions,

            "timestamp":
            str(datetime.utcnow())
        }

        runtime_context[
            "runtime_stability_report"
        ] = final_report

        self.stability_history.append(
            final_report
        )

        self.stability_state[
            "stability_cycles"
        ] += 1

        return runtime_context

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "stability_cycles":
            self.stability_state[
                "stability_cycles"
            ],

            "stability_history":
            len(
                self.stability_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL STABILITY MONITOR
# ============================================

runtime_stability_monitor = (
    RuntimeStabilityMonitor()
)