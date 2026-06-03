# ============================================
# NEXRYN HORIZON MEMORY MANAGER
# ============================================

from datetime import datetime


class HorizonMemoryManager:

    def __init__(self):

        self.horizon_history = []

    def route_short_term(self, context):

        return [
            key
            for key in [
                "input_grid",
                "output_grid",
                "predicted_output",
                "evaluation_result",
                "winner_hypothesis"
            ]
            if key in context
        ]

    def route_mid_term(self, context):

        return [
            key
            for key in [
                "execution_trace",
                "reasoning_trace",
                "operator_reward_report",
                "safe_concept_folding_report"
            ]
            if key in context
        ]

    def route_long_term(self, context):

        return [
            key
            for key in [
                "semantic_graph",
                "semantic_pointer_report",
                "cognitive_identity_report",
                "identity_core_report"
            ]
            if key in context
        ]

    def archive_permanent_patterns(self, context):

        return [
            key
            for key in [
                "operator_weights",
                "semantic_index_report",
                "cognitive_failure_memory_report"
            ]
            if key in context
        ]

    def decay_temporary_context(self, context):

        return [
            key
            for key in context.keys()
            if str(
                key
            ).startswith(
                (
                    "debug",
                    "temporary",
                    "scratch"
                )
            )
        ][:16]

    def run_cycle(self, context):

        report = {
            "runtime":
            "multi_horizon_memory",

            "short_horizon":
            self.route_short_term(
                context
            ),

            "mid_horizon":
            self.route_mid_term(
                context
            ),

            "long_horizon":
            self.route_long_term(
                context
            ),

            "permanent_patterns":
            self.archive_permanent_patterns(
                context
            ),

            "decay_candidates":
            self.decay_temporary_context(
                context
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.horizon_history.append(
            report
        )

        self.horizon_history = (
            self.horizon_history[-32:]
        )

        return report


horizon_memory_manager = (
    HorizonMemoryManager()
)
