def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class SemanticEnergyBudget:

    def compute(self, context):

        economy = context.get(
            "cognitive_energy_economy_report",
            {},
        )

        energy_cost = _clamp(
            economy.get(
                "total_energy_cost",
                0.0,
            )
        )

        memory_pressure = _clamp(
            context.get(
                "memory_pressure_score",
                0.0,
            )
        )

        semantic_spine = context.get(
            "semantic_spine_report",
            {},
        )

        spine_repair_cost = _clamp(
            1.0
            -
            semantic_spine.get(
                "spine_integrity",
                1.0,
            )
        )

        budget_load = _clamp(
            energy_cost * 0.38
            +
            memory_pressure * 0.28
            +
            spine_repair_cost * 0.34
        )

        return {
            "system":
            "semantic_energy_budget",

            "energy_cost":
            energy_cost,

            "memory_pressure":
            memory_pressure,

            "spine_repair_cost":
            spine_repair_cost,

            "semantic_budget_load":
            budget_load,

            "budget_state":
            (
                "semantic_budget_overdrawn"
                if budget_load >= 0.72
                else "semantic_budget_constrained"
                if budget_load >= 0.44
                else "semantic_budget_balanced"
            ),
        }
