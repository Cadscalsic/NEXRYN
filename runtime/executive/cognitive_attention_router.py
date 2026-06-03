# ============================================
# NEXRYN COGNITIVE ATTENTION ROUTER
# ============================================

from datetime import datetime


class CognitiveAttentionRouter:

    def __init__(self):

        self.routing_history = []

    def route(
        self,
        context
    ):

        attention = context.get(
            "dynamic_attention_allocation",
            {}
        )

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        memory = context.get(
            "hierarchical_memory_architecture_report",
            {}
        )

        saturation = attention.get(
            "attention_saturation",
            0.0
        )

        memory_pressure = memory.get(
            "combined_memory_pressure",
            0.0
        )

        focus_window = attention.get(
            "priority_attention",
            []
        )

        semantic_focus = attention.get(
            "semantic_focus_window",
            []
        )

        actions = []

        if saturation >= 0.70:

            actions.append(
                "lock_priority_attention"
            )

        if memory_pressure >= 0.75:

            actions.append(
                "route_low_priority_context_to_compression"
            )

        if governance.get(
            "signals",
            {}
        ).get(
            "reasoning_overrun",
            False
        ):

            actions.append(
                "route_excess_reasoning_to_latent_memory"
            )

        if len(
            semantic_focus
        ) > 8:

            actions.append(
                "narrow_semantic_attention"
            )

        report = {
            "router":
            "cognitive_attention",

            "attention_state":
            (
                "saturated"
                if saturation >= 0.70
                else "loaded"
                if saturation >= 0.50
                else "stable"
            ),

            "focus_window_count":
            len(
                focus_window
            ),

            "semantic_focus_count":
            len(
                semantic_focus
            ),

            "routed_actions":
            actions,

            "attention_saturation":
            saturation,

            "memory_pressure":
            memory_pressure,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.routing_history.append(
            report
        )

        self.routing_history = (
            self.routing_history[-32:]
        )

        return report

    def build_report(self):

        latest = (
            self.routing_history[-1]
            if self.routing_history
            else {}
        )

        return {
            "routing_cycles":
            len(
                self.routing_history
            ),

            "latest_state":
            latest.get(
                "attention_state",
                "unknown"
            ),

            "latest_action_count":
            len(
                latest.get(
                    "routed_actions",
                    []
                )
            )
        }


cognitive_attention_router = (
    CognitiveAttentionRouter()
)
