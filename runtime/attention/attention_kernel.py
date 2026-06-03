# ============================================
# NEXRYN RUNTIME ATTENTION KERNEL
# ============================================

from datetime import datetime


class AttentionKernel:

    def __init__(self):

        self.kernel_history = []

    def allocate_focus(self, context):

        attention = context.get(
            "dynamic_attention_allocation",
            {}
        )

        focus = attention.get(
            "priority_attention",
            []
        )

        return focus[:24]

    def decay_low_priority(self, context):

        attention = context.get(
            "dynamic_attention_allocation",
            {}
        )

        pruning = attention.get(
            "adaptive_context_pruning",
            {}
        )

        return pruning.get(
            "safe_to_prune",
            []
        )

    def protect_focus_window(self, context):

        focus = self.allocate_focus(
            context
        )

        return [
            item.get(
                "key"
            )
            for item in focus
            if item.get(
                "priority",
                0.0
            ) >= 0.70
        ]

    def reroute_overflow(self, context):

        memory = context.get(
            "hierarchical_memory_architecture_report",
            {}
        )

        layers = memory.get(
            "layers",
            {}
        )

        return [
            layer_name
            for layer_name, layer in layers.items()
            if layer.get(
                "pressure",
                0.0
            ) >= 0.85
        ]

    def activate_priority_context(self, context):

        protected = self.protect_focus_window(
            context
        )

        return {
            key:
            context.get(
                key
            )
            for key in protected
            if key in context
        }

    def compress_background_context(self, context):

        decay_candidates = self.decay_low_priority(
            context
        )

        return {
            "candidate_count":
            len(
                decay_candidates
            ),

            "candidates":
            decay_candidates[:16],

            "policy":
            (
                "compress_background"
                if decay_candidates
                else "retain_background"
            )
        }

    def regulate_attention_entropy(self, context):

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        saturation = (
            context.get(
                "dynamic_attention_allocation",
                {}
            )
            .get(
                "attention_saturation",
                0.0
            )
        )

        entropy = (
            governance.get(
                "signals",
                {}
            )
            .get(
                "projected_entropy",
                0
            )
        )

        attention_entropy = round(
            min(
                saturation * 0.55
                +
                min(
                    entropy / 12,
                    1.0
                )
                * 0.45,
                1.0
            ),
            4
        )

        return {
            "attention_entropy":
            attention_entropy,

            "state":
            (
                "critical"
                if attention_entropy >= 0.75
                else "elevated"
                if attention_entropy >= 0.50
                else "stable"
            )
        }

    def run_cycle(self, context):

        active_context = self.activate_priority_context(
            context
        )

        background = self.compress_background_context(
            context
        )

        entropy = self.regulate_attention_entropy(
            context
        )

        report = {
            "kernel":
            "attention",

            "focus_window":
            self.allocate_focus(
                context
            ),

            "protected_focus_keys":
            list(
                active_context.keys()
            ),

            "overflow_routes":
            self.reroute_overflow(
                context
            ),

            "background_compression":
            background,

            "attention_energy_allocation":
            {
                "focus_energy":
                0.60,

                "semantic_activation_energy":
                0.20,

                "background_energy":
                0.10,

                "recovery_energy":
                0.10
            },

            "entropy_regulation":
            entropy,

            "actions":
            [
                "protect_focus_window",
                "reroute_attention_overflow"
            ]
            +
            (
                [
                    "compress_background_context"
                ]
                if background.get(
                    "candidate_count",
                    0
                )
                else []
            )
            +
            (
                [
                    "reduce_attention_entropy"
                ]
                if entropy.get(
                    "state"
                )
                in [
                    "elevated",
                    "critical"
                ]
                else []
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.kernel_history.append(
            report
        )

        self.kernel_history = (
            self.kernel_history[-32:]
        )

        return report


attention_kernel = (
    AttentionKernel()
)
