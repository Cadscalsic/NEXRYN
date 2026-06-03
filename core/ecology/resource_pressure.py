# ============================================
# NEXRYN RESOURCE PRESSURE
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class ResourcePressure:

    def compute(self, context):

        energy = context.get(
            "cognitive_energy_economy_report",
            {},
        )

        total_cost = _clamp(
            energy.get(
                "total_energy_cost",
                context.get(
                    "total_energy_cost",
                    0.0,
                ),
            )
            /
            32
        )

        attention = context.get(
            "attention_kernel_report",
            {},
        )

        attention_load = _clamp(
            attention.get(
                "attention_saturation",
                context.get(
                    "attention_saturation",
                    0.0,
                ),
            ),
        )

        budget_market = context.get(
            "recursive_budget_market_report",
            {},
        )

        remaining_budget = _clamp(
            budget_market.get(
                "remaining_budget",
                context.get(
                    "remaining_budget",
                    1.0,
                ),
            )
            /
            max(
                budget_market.get(
                    "base_recursion_budget",
                    1.0,
                ),
                1.0,
            )
        )

        memory_pressure = _clamp(
            context.get(
                "working_memory_pressure",
                context.get(
                    "memory_pressure",
                    0.0,
                ),
            ),
        )

        pressure = _clamp(
            total_cost * 0.30
            +
            attention_load * 0.26
            +
            (
                1.0 - remaining_budget
            )
            * 0.24
            +
            memory_pressure * 0.20
        )

        return {
            "system":
            "resource_pressure",

            "resource_pressure":
            pressure,

            "energy_cost_pressure":
            total_cost,

            "attention_load":
            attention_load,

            "remaining_budget_ratio":
            remaining_budget,

            "memory_pressure":
            memory_pressure,

            "scarcity_state":
            (
                "severe_scarcity"
                if pressure >= 0.72
                else "constrained"
                if pressure >= 0.42
                else "available"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
