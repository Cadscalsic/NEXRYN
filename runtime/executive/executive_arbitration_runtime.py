# ============================================
# NEXRYN EXECUTIVE ARBITRATION RUNTIME
# ============================================

from datetime import datetime


class ExecutiveArbitrationRuntime:

    def __init__(self):

        self.arbitration_history = []

    def arbitrate(
        self,
        context
    ):

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        energy = context.get(
            "cognitive_energy_economy_report",
            {}
        )

        memory = context.get(
            "hierarchical_memory_architecture_report",
            {}
        )

        folding = context.get(
            "safe_concept_folding_report",
            {}
        )

        attention = context.get(
            "dynamic_attention_allocation",
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

        identity = context.get(
            "cognitive_identity_report",
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

        entropy = context.get(
            "cognitive_entropy_report",
            {}
        )

        scheduler = context.get(
            "cognitive_scheduler_report",
            {}
        )

        latent = context.get(
            "latent_reservoir_report",
            {}
        )

        actions = []

        actions.extend(
            governance.get(
                "actions",
                []
            )
        )

        actions.extend(
            energy.get(
                "actions",
                []
            )
        )

        actions.extend(
            attention_router.get(
                "routed_actions",
                []
            )
        )

        actions.extend(
            compression.get(
                "actions",
                []
            )
        )

        actions.extend(
            identity.get(
                "actions",
                []
            )
        )

        actions.extend(
            attention_kernel.get(
                "actions",
                []
            )
        )

        actions.extend(
            entropy.get(
                "stabilization_actions",
                []
            )
        )

        actions.extend(
            scheduler.get(
                "scheduled_actions",
                []
            )
        )

        if memory.get(
            "combined_memory_pressure",
            0.0
        ) >= 0.70:

            actions.append(
                "rebalance_memory_layers"
            )

        if folding.get(
            "folding_pressure",
            0.0
        ) >= 0.50:

            actions.append(
                "prefer_aliasing_over_merging"
            )

        if attention.get(
            "attention_saturation",
            0.0
        ) >= 0.70:

            actions.append(
                "protect_focus_window"
            )

        if semantic_pointer.get(
            "alias_count",
            0
        ) > 0:

            actions.append(
                "prefer_semantic_pointers"
            )

        if latent.get(
            "latent_population",
            0
        ) >= 24:

            actions.append(
                "compress_latent_reservoir"
            )

        unique_actions = []

        for action in actions:

            if action not in unique_actions:

                unique_actions.append(
                    action
                )

        executive_mode = (
            "protective_arbitration"
            if any(
                action in unique_actions
                for action in [
                    "defer_noncritical_recursion",
                    "rebalance_memory_layers",
                    "protect_focus_window",
                    "prefer_aliasing_over_merging",
                    "preserve_causal_identity",
                    "route_low_priority_context_to_compression"
                    ,
                    "freeze_unstable_merges",
                    "stabilize_semantic_activation"
                ]
            )
            else "balanced_arbitration"
        )

        report = {
            "runtime":
            "executive_arbitration",

            "executive_mode":
            executive_mode,

            "selected_actions":
            unique_actions,

            "arbitration_inputs":
            {
                "governance_state":
                governance.get(
                    "executive_state",
                    "unknown"
                ),

                "energy_state":
                energy.get(
                    "energy_state",
                    "unknown"
                ),

                "memory_pressure":
                memory.get(
                    "combined_memory_pressure",
                    0.0
                ),

                "folding_pressure":
                folding.get(
                    "folding_pressure",
                    0.0
                ),

                "attention_saturation":
                attention.get(
                    "attention_saturation",
                    0.0
                ),

                "identity_risk":
                identity.get(
                    "identity_risk",
                    0.0
                ),

                "semantic_pointer_count":
                semantic_pointer.get(
                    "pointer_count",
                    0
                ),

                "compression_mode":
                compression.get(
                    "compression_mode",
                    "unknown"
                ),

                "runtime_entropy":
                entropy.get(
                    "runtime_entropy",
                    0.0
                ),

                "projected_overload":
                scheduler.get(
                    "projected_overload",
                    0.0
                )
            },

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.arbitration_history.append(
            report
        )

        self.arbitration_history = (
            self.arbitration_history[-32:]
        )

        return report

    def build_report(self):

        latest = (
            self.arbitration_history[-1]
            if self.arbitration_history
            else {}
        )

        return {
            "arbitration_cycles":
            len(
                self.arbitration_history
            ),

            "latest_mode":
            latest.get(
                "executive_mode",
                "unknown"
            ),

            "latest_action_count":
            len(
                latest.get(
                    "selected_actions",
                    []
                )
            )
        }


executive_arbitration_runtime = (
    ExecutiveArbitrationRuntime()
)
