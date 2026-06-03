# ============================================
# NEXRYN ADAPTIVE EXPLORATION CONTROLLER
# ============================================

from datetime import datetime


# ============================================
# ADAPTIVE EXPLORATION CONTROLLER
# ============================================

class AdaptiveExplorationController:

    # ========================================
    # INITIALIZE
    # ========================================

    def __init__(self):

        # ====================================
        # EXPLORATION STATE
        # ====================================

        self.exploration_state = {

            "adaptive_exploration":
            True,

            "mutation_governance":
            True,

            "semantic_stabilization":
            True,

            "exploration_regulation":
            True,

            "cognitive_divergence_control":
            True,

            "exploration_cycles":
            0
        }

        # ====================================
        # EXPLORATION HISTORY
        # ====================================

        self.exploration_history = []

    # ========================================
    # ANALYZE EXPLORATION
    # ========================================

    def analyze_exploration(

        self,

        runtime_context
    ):

        recursive_report = (

            runtime_context.get(
                "recursive_report"
            )

            or {}
        )

        mutation_detected = (

            recursive_report.get(
                "mutation_detected",
                False
            )
        )

        exploration_detected = (

            recursive_report.get(
                "exploration_detected",
                False
            )
        )

        search_result = (

            runtime_context.get(
                "search_result"
            )

            or {}
        )

        path_count = (

            search_result.get(
                "path_count",
                0
            )
        )

        inference_report = (

            runtime_context.get(
                "inference_report"
            )

            or {}
        )

        cognitive_pressure = (

            inference_report.get(
                "cognitive_pressure",
                0.0
            )
        )

        return {

            "mutation_detected":
            mutation_detected,

            "exploration_detected":
            exploration_detected,

            "search_paths":
            path_count,

            "cognitive_pressure":
            cognitive_pressure,

            "exploration_state":
            self.classify_exploration_state(

                mutation_detected,

                path_count,

                cognitive_pressure
            )
        }

    # ========================================
    # CLASSIFY EXPLORATION STATE
    # ========================================

    def classify_exploration_state(

        self,

        mutation_detected,

        path_count,

        cognitive_pressure
    ):

        if (

            mutation_detected
            and path_count >= 10
            and cognitive_pressure >= 0.8
        ):

            return "critical"

        if (

            path_count >= 6
            or cognitive_pressure >= 0.7
        ):

            return "high"

        if (

            path_count >= 3
            or mutation_detected
        ):

            return "moderate"

        return "stable"

    # ========================================
    # BUILD EXPLORATION ACTIONS
    # ========================================

    def build_exploration_actions(

        self,

        exploration_report
    ):

        actions = []

        exploration_state = (

            exploration_report.get(
                "exploration_state"
            )
        )

        # ====================================
        # CRITICAL EXPLORATION
        # ====================================

        if exploration_state == "critical":

            actions.extend([

                {

                    "action":
                    "limit_mutation_generation",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "reduce_search_branching",

                    "priority":
                    "critical"
                },

                {

                    "action":
                    "activate_semantic_stabilization",

                    "priority":
                    "high"
                }
            ])

        # ====================================
        # HIGH EXPLORATION
        # ====================================

        elif exploration_state == "high":

            actions.extend([

                {

                    "action":
                    "stabilize_exploration_routes",

                    "priority":
                    "high"
                },

                {

                    "action":
                    "reduce_recursive_search",

                    "priority":
                    "medium"
                }
            ])

        # ====================================
        # MODERATE EXPLORATION
        # ====================================

        elif exploration_state == "moderate":

            actions.append({

                "action":
                "maintain_adaptive_exploration",

                "priority":
                "medium"
            })

        # ====================================
        # STABLE EXPLORATION
        # ====================================

        else:

            actions.append({

                "action":
                "allow_controlled_exploration",

                "priority":
                "low"
            })

        return actions

    # ========================================
    # RUN EXPLORATION CYCLE
    # ========================================

    def run_exploration_cycle(

        self,

        runtime_context
    ):

        exploration_report = (

            self.analyze_exploration(
                runtime_context
            )
        )

        exploration_actions = (

            self.build_exploration_actions(
                exploration_report
            )
        )

        final_report = {

            "exploration_analysis":
            exploration_report,

            "exploration_actions":
            exploration_actions,

            "timestamp":
            str(datetime.utcnow())
        }

        runtime_context[
            "adaptive_exploration_report"
        ] = final_report

        self.exploration_history.append(
            final_report
        )

        self.exploration_state[
            "exploration_cycles"
        ] += 1

        return runtime_context

    # ========================================
    # BUILD REPORT
    # ========================================

    def build_report(self):

        return {

            "exploration_cycles":
            self.exploration_state[
                "exploration_cycles"
            ],

            "exploration_history":
            len(
                self.exploration_history
            ),

            "timestamp":
            str(datetime.utcnow())
        }


# ============================================
# GLOBAL EXPLORATION CONTROLLER
# ============================================

adaptive_exploration_controller = (
    AdaptiveExplorationController()
)