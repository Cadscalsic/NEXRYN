# ============================================
# NEXRYN COGNITIVE ENERGY ECONOMY
# ============================================

from datetime import datetime


class CognitiveEnergyEconomy:

    def __init__(self):

        self.energy_history = []

    def compute_energy_budget(
        self,
        context
    ):

        inference_report = context.get(
            "inference_report",
            {}
        )

        governance_report = context.get(
            "cognitive_governance_report",
            {}
        )

        attention = context.get(
            "dynamic_attention_allocation",
            {}
        )

        raw_depth = inference_report.get(
            "raw_reasoning_depth",
            context.get(
                "raw_reasoning_depth",
                0
            )
        )

        regulated_depth = inference_report.get(
            "reasoning_depth",
            context.get(
                "regulated_reasoning_depth",
                0
            )
        )

        overrun_cost = max(
            raw_depth - regulated_depth,
            0
        )

        semantic_graph = context.get(
            "semantic_graph",
            {}
        )

        semantic_cost = semantic_graph.get(
            "concept_count",
            0
        ) * 0.08

        attention_cost = attention.get(
            "attention_saturation",
            0.0
        ) * 0.30

        memory_pressure = (
            governance_report
            .get(
                "cognitive_budget",
                {}
            )
            .get(
                "memory_pressure",
                0.0
            )
        )

        total_cost = round(
            min(
                overrun_cost * 0.07
                +
                semantic_cost
                +
                attention_cost
                +
                memory_pressure * 0.25,
                1.0
            ),
            4
        )

        state = (
            "critical"
            if total_cost >= 0.80
            else "constrained"
            if total_cost >= 0.60
            else "balanced"
            if total_cost >= 0.35
            else "ample"
        )

        allocation = {
            "reasoning_energy":
            round(
                max(
                    0.15,
                    0.45 - total_cost * 0.20
                ),
                4
            ),

            "semantic_energy":
            round(
                max(
                    0.15,
                    0.30 - total_cost * 0.10
                ),
                4
            ),

            "execution_energy":
            0.25,

            "exploration_energy":
            round(
                max(
                    0.02,
                    0.15 - total_cost * 0.12
                ),
                4
            )
        }

        actions = []

        if overrun_cost > 0:

            actions.append(
                "charge_reasoning_overrun"
            )

        if total_cost >= 0.60:

            actions.append(
                "reduce_exploration_energy"
            )

            actions.append(
                "prefer_cached_semantic_routes"
            )

        if total_cost >= 0.80:

            actions.append(
                "defer_noncritical_recursion"
            )

        report = {
            "economy":
            "cognitive_energy",

            "raw_reasoning_depth":
            raw_depth,

            "regulated_reasoning_depth":
            regulated_depth,

            "reasoning_overrun_cost":
            overrun_cost,

            "total_energy_cost":
            total_cost,

            "energy_state":
            state,

            "allocation":
            allocation,

            "actions":
            actions,

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.energy_history.append(
            report
        )

        self.energy_history = self.energy_history[-32:]

        return report

    def build_report(self):

        latest = (
            self.energy_history[-1]
            if self.energy_history
            else {}
        )

        return {
            "economy_cycles":
            len(
                self.energy_history
            ),

            "latest_energy_state":
            latest.get(
                "energy_state",
                "unknown"
            ),

            "latest_total_energy_cost":
            latest.get(
                "total_energy_cost",
                0.0
            )
        }


cognitive_energy_economy = (
    CognitiveEnergyEconomy()
)
