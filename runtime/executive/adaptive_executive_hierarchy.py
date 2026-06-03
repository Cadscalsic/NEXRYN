# ============================================
# NEXRYN ADAPTIVE EXECUTIVE HIERARCHY
# ============================================

from datetime import datetime


class AdaptiveExecutiveHierarchy:

    def __init__(self):

        self.hierarchy_history = []

    def build_hierarchy(
        self,
        context
    ):

        arbitration = context.get(
            "executive_arbitration_report",
            {}
        )

        identity = context.get(
            "cognitive_identity_report",
            {}
        )

        attention_router = context.get(
            "cognitive_attention_router_report",
            {}
        )

        compression = context.get(
            "memory_compression_runtime_report",
            {}
        )

        semantic_pointer = context.get(
            "semantic_pointer_report",
            {}
        )

        attention_kernel = context.get(
            "attention_kernel_report",
            {}
        )

        scheduler = context.get(
            "cognitive_scheduler_report",
            {}
        )

        entropy = context.get(
            "cognitive_entropy_report",
            {}
        )

        command_layers = [
            {
                "layer":
                "identity_guardian",

                "priority":
                1,

                "state":
                identity.get(
                    "identity_state",
                    "unknown"
                )
            },
            {
                "layer":
                "executive_arbitration",

                "priority":
                2,

                "state":
                arbitration.get(
                    "executive_mode",
                    "unknown"
                )
            },
            {
                "layer":
                "attention_kernel",

                "priority":
                3,

                "state":
                attention_kernel.get(
                    "entropy_regulation",
                    {}
                ).get(
                    "state",
                    "unknown"
                )
            },
            {
                "layer":
                "cognitive_scheduler",

                "priority":
                4,

                "state":
                scheduler.get(
                    "recursion_policy",
                    "unknown"
                )
            },
            {
                "layer":
                "attention_router",

                "priority":
                5,

                "state":
                attention_router.get(
                    "attention_state",
                    "unknown"
                )
            },
            {
                "layer":
                "memory_compression",

                "priority":
                6,

                "state":
                compression.get(
                    "compression_mode",
                    "unknown"
                )
            },
            {
                "layer":
                "entropy_engine",

                "priority":
                7,

                "state":
                entropy.get(
                    "entropy_state",
                    "unknown"
                )
            },
            {
                "layer":
                "semantic_pointer",

                "priority":
                8,

                "state":
                semantic_pointer.get(
                    "policy",
                    "unknown"
                )
            }
        ]

        executive_state = (
            "identity_protection"
            if identity.get(
                "identity_risk",
                0.0
            ) >= 0.60
            else "protective_control"
            if arbitration.get(
                "executive_mode"
            ) == "protective_arbitration"
            else "balanced_control"
        )

        report = {
            "hierarchy":
            "adaptive_executive",

            "executive_state":
            executive_state,

            "command_layers":
            command_layers,

            "top_priority":
            command_layers[0],

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.hierarchy_history.append(
            report
        )

        self.hierarchy_history = (
            self.hierarchy_history[-32:]
        )

        return report


adaptive_executive_hierarchy = (
    AdaptiveExecutiveHierarchy()
)
