# ============================================
# NEXRYN EXECUTIVE COGNITIVE SCHEDULER
# ============================================

from datetime import datetime


class CognitiveScheduler:

    def __init__(self):

        self.schedule_history = []

    def predict_overload(self, context):

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        memory = context.get(
            "hierarchical_memory_architecture_report",
            {}
        )

        attention = context.get(
            "attention_kernel_report",
            {}
        )

        entropy = context.get(
            "cognitive_entropy_report",
            {}
        )

        overload = round(
            min(
                memory.get(
                    "combined_memory_pressure",
                    0.0
                )
                * 0.30
                +
                governance.get(
                    "signals",
                    {}
                ).get(
                    "attention_saturation",
                    0.0
                )
                * 0.25
                +
                attention.get(
                    "entropy_regulation",
                    {}
                ).get(
                    "attention_entropy",
                    0.0
                )
                * 0.25
                +
                entropy.get(
                    "runtime_entropy",
                    0.0
                )
                * 0.20,
                1.0
            ),
            4
        )

        return overload

    def schedule_reasoning_budget(self, overload):

        if overload >= 0.75:

            return 3

        if overload >= 0.55:

            return 5

        return 8

    def regulate_recursion(self, overload):

        return (
            "pause_noncritical_recursion"
            if overload >= 0.75
            else "shallow_recursion_only"
            if overload >= 0.55
            else "normal_recursion"
        )

    def allocate_cognitive_energy(self, overload):

        if overload >= 0.75:

            return {
                "reasoning":
                0.20,

                "execution":
                0.30,

                "semantic":
                0.20,

                "recovery":
                0.30
            }

        return {
            "reasoning":
            0.35,

            "execution":
            0.30,

            "semantic":
            0.20,

            "recovery":
            0.15
        }

    def throttle_exploration(self, overload):

        return (
            0.02
            if overload >= 0.75
            else 0.05
            if overload >= 0.55
            else 0.10
        )

    def rebalance_runtime(self, context):

        overload = self.predict_overload(
            context
        )

        actions = []

        if overload >= 0.55:

            actions.extend([
                "reduce_recursion_budget",
                "throttle_exploration",
                "schedule_memory_compression"
            ])

        if overload >= 0.75:

            actions.extend([
                "flush_latent_overflow",
                "stabilize_semantic_activation"
            ])

        report = {
            "scheduler":
            "executive_cognitive",

            "projected_overload":
            overload,

            "reasoning_depth_limit":
            self.schedule_reasoning_budget(
                overload
            ),

            "recursion_policy":
            self.regulate_recursion(
                overload
            ),

            "energy_allocation":
            self.allocate_cognitive_energy(
                overload
            ),

            "exploration_rate":
            self.throttle_exploration(
                overload
            ),

            "scheduled_actions":
            actions,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.schedule_history.append(
            report
        )

        self.schedule_history = (
            self.schedule_history[-32:]
        )

        return report


cognitive_scheduler = (
    CognitiveScheduler()
)
