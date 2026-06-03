# ============================================
# NEXRYN FAILURE ANALYZER
# ============================================


# ============================================
# FAILURE ANALYZER
# ============================================

class FailureAnalyzer:

    def __init__(self):

        self.failure_history = []

    # ============================================
    # ANALYZE FAILURE
    # ============================================

    def analyze_failure(

        self,

        cognitive_cycle,

        evaluation_result
    ):

        reasoning = cognitive_cycle.get(
            "reasoning",
            {}
        )

        semantics = cognitive_cycle.get(
            "semantics",
            {}
        )

        routing = cognitive_cycle.get(
            "routing",
            {}
        )

        execution = cognitive_cycle.get(
            "execution",
            {}
        )

        analysis = {

            "failure_detected":
            not evaluation_result.get(
                "success",
                False
            ),

            "accuracy":
            evaluation_result.get(
                "accuracy",
                0.0
            ),

            "success_state":
            evaluation_result.get(
                "success_state",
                "FAILURE"
            ),

            "partial_success_detected":
            evaluation_result.get(
                "partial_success",
                False
            ) is True,

            "reasoning_depth":
            reasoning.get(
                "reasoning_depth",
                0
            ),

            "cognitive_complexity":
            reasoning.get(
                "cognitive_complexity",
                "unknown"
            ),

            "semantic_density":
            semantics.get(
                "concept_count",
                0
            ),

            "route_count":
            routing.get(
                "route_count",
                0
            ),

            "execution_nodes":
            execution.get(
                "node_count",
                0
            ),

            "failure_causes":
            [],

            "diagnostic_signals":
            []
        }

        # ====================================
        # NO FAILURE DETECTED
        # ====================================

        if not analysis[
            "failure_detected"
        ]:

            analysis[
                "failure_causes"
            ] = []

            return analysis

        # ====================================
        # FAILURE DIAGNOSIS
        # ====================================

        if analysis[
            "accuracy"
        ] < 0.5:

            analysis[
                "failure_causes"
            ].append(

                "severe_prediction_failure"
            )

        if analysis[
            "reasoning_depth"
        ] > 15:

            analysis[
                "failure_causes"
            ].append(

                "reasoning_overexpansion"
            )

        if analysis[
            "semantic_density"
        ] < 2:

            analysis[
                "diagnostic_signals"
            ].append(

                "low_semantic_density"
            )

        if (
            analysis[
                "semantic_density"
            ] < 2
            and analysis[
                "accuracy"
            ] < 0.5
        ):

            analysis[
                "failure_causes"
            ].append(

                "weak_semantic_abstraction"
            )

        if analysis[
            "route_count"
        ] > 10:

            analysis[
                "failure_causes"
            ].append(

                "routing_overload"
            )

        if analysis[
            "execution_nodes"
        ] > 20:

            analysis[
                "failure_causes"
            ].append(

                "execution_complexity_overload"
            )

        if (
            not analysis[
                "failure_causes"
            ]
            and analysis[
                "partial_success_detected"
            ]
        ):

            analysis[
                "failure_causes"
            ].append(

                "partial_success_residual_mismatch"
            )

        if (
            not analysis[
                "failure_causes"
            ]
            and analysis[
                "accuracy"
            ] >= 0.5
        ):

            analysis[
                "failure_causes"
            ].append(

                "localized_prediction_mismatch"
            )

        if not analysis[
            "failure_causes"
        ]:

            analysis[
                "failure_causes"
            ].append(

                "unknown_failure_pattern"
            )

        return analysis

    # ============================================
    # BUILD RECOVERY PLAN
    # ============================================

    def build_recovery_plan(

        self,

        failure_analysis
    ):

        recovery_actions = []

        causes = failure_analysis.get(
            "failure_causes",
            []
        )

        for cause in causes:

            if cause == (
                "severe_prediction_failure"
            ):

                recovery_actions.append(

                    "increase_search_diversity"
                )

            elif cause == (
                "reasoning_overexpansion"
            ):

                recovery_actions.append(

                    "reduce_reasoning_depth"
                )

            elif cause == (
                "weak_semantic_abstraction"
            ):

                recovery_actions.append(

                    "expand_semantic_mapping"
                )

            elif cause == (
                "routing_overload"
            ):

                recovery_actions.append(

                    "simplify_routing_plan"
                )

            elif cause == (
                "execution_complexity_overload"
            ):

                recovery_actions.append(

                    "reduce_execution_graph"
                )

            elif cause == (
                "partial_success_residual_mismatch"
            ):

                recovery_actions.append(

                    "refine_partial_success_residual"
                )

            elif cause == (
                "localized_prediction_mismatch"
            ):

                recovery_actions.append(

                    "inspect_residual_prediction_mismatch"
                )

            else:

                recovery_actions.append(

                    "perform_adaptive_reflection"
                )

        recovery_plan = {

            "failure_detected":
            failure_analysis.get(
                "failure_detected",
                False
            ),

            "recovery_actions":
            recovery_actions,

            "action_count":
            len(recovery_actions)
        }

        return recovery_plan

    # ============================================
    # STORE FAILURE
    # ============================================

    def store_failure(

        self,

        failure_analysis
    ):

        self.failure_history.append(

            failure_analysis
        )

    # ============================================
    # BUILD FAILURE SUMMARY
    # ============================================

    def build_failure_summary(self):

        total_failures = len(
            self.failure_history
        )

        severe_failures = 0

        for failure in self.failure_history:

            if failure.get(
                "accuracy",
                1.0
            ) < 0.5:

                severe_failures += 1

        summary = {

            "total_failures":
            total_failures,

            "severe_failures":
            severe_failures,

            "latest_failure":

            self.failure_history[-1]

            if self.failure_history

            else {}
        }

        return summary
