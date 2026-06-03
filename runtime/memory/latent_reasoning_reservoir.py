# ============================================
# NEXRYN LATENT REASONING RESERVOIR
# ============================================

from datetime import datetime


# ============================================
# LATENT REASONING RESERVOIR
# ============================================

class LatentReasoningReservoir:

    def __init__(self):

        self.hidden_reasoning = []

        self.reactivation_history = []

    # ============================================
    # STORE HIDDEN REASONING
    # ============================================

    def store_hidden_reasoning(
        self,
        reasoning_trace,
        visible_depth,
        reason,
        context_signals=None
    ):

        if not isinstance(
            reasoning_trace,
            list
        ):

            reasoning_trace = []

        hidden_trace = reasoning_trace[
            visible_depth:
        ]

        event = {
            "event_id":
            len(
                self.hidden_reasoning
            )
            +
            1,

            "visible_depth":
            visible_depth,

            "hidden_depth":
            len(
                hidden_trace
            ),

            "hidden_trace":
            hidden_trace,

            "reason":
            reason,

            "context_signals":
            context_signals
            or {},

            "reactivated":
            False,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        if hidden_trace:

            self.hidden_reasoning.append(
                event
            )

            self.hidden_reasoning = (
                self.hidden_reasoning[-32:]
            )

        return event

    # ============================================
    # REACTIVATE IF NEEDED
    # ============================================

    def reactivate_if_needed(
        self,
        context
    ):

        if not isinstance(
            context,
            dict
        ):

            context = {}

        evaluation_result = context.get(
            "evaluation_result",
            {}
        )

        anticipation = context.get(
            "world_model_anticipation",
            {}
        )

        uncertainty = (
            anticipation
            .get(
                "uncertainty_report",
                {}
            )
            .get(
                "simulation_uncertainty",
                0.0
            )
        )

        should_reactivate = (
            not evaluation_result.get(
                "success",
                True
            )
            or
            evaluation_result.get(
                "accuracy",
                1.0
            ) < 0.95
            or
            uncertainty > 0.45
        )

        if (
            not should_reactivate
            or
            not self.hidden_reasoning
        ):

            return {
                "reactivated":
                False,

                "reason":
                "stable_execution"
            }

        candidate = self.hidden_reasoning[-1]

        candidate[
            "reactivated"
        ] = True

        event = {
            "reactivated":
            True,

            "source_event_id":
            candidate.get(
                "event_id"
            ),

            "hidden_depth":
            candidate.get(
                "hidden_depth",
                0
            ),

            "reactivated_trace":
            candidate.get(
                "hidden_trace",
                []
            ),

            "reason":
            "evaluation_or_uncertainty_pressure",

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.reactivation_history.append(
            event
        )

        self.reactivation_history = (
            self.reactivation_history[-32:]
        )

        return event

    # ============================================
    # BUILD REPORT
    # ============================================

    def build_report(self):

        return {
            "reservoir_size":
            len(
                self.hidden_reasoning
            ),

            "reactivation_count":
            len(
                self.reactivation_history
            ),

            "latest_hidden_reasoning":
            (
                self.hidden_reasoning[-1]
                if self.hidden_reasoning
                else {}
            ),

            "latest_reactivation":
            (
                self.reactivation_history[-1]
                if self.reactivation_history
                else {}
            )
        }


# ============================================
# GLOBAL RESERVOIR
# ============================================

latent_reasoning_reservoir = (
    LatentReasoningReservoir()
)
