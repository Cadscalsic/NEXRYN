# ============================================
# NEXRYN SIMULATION BUDGET
# ============================================


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


class SimulationBudget:

    def allocate(self, context):

        sandbox = context.get(
            "safe_exploratory_sandbox_report",
            {},
        )

        worlds = context.get(
            "recursive_simulation_worlds_report",
            {},
        )

        simulation_count = sandbox.get(
            "simulation_count",
            context.get(
                "simulation_count",
                0,
            ),
        )

        world_count = worlds.get(
            "world_count",
            context.get(
                "world_count",
                0,
            ),
        )

        entropy = context.get(
            "runtime_entropy",
            context.get(
                "cognitive_entropy_report",
                {},
            ).get(
                "runtime_entropy",
                0.0,
            ),
        )

        pressure = _clamp(
            simulation_count / 24 * 0.45
            +
            world_count / 8 * 0.35
            +
            entropy * 0.20
        )

        max_worlds = (
            2
            if pressure >= 0.75
            else 4
            if pressure >= 0.50
            else 6
        )

        return {
            "system":
            "simulation_budget",

            "simulation_count":
            simulation_count,

            "world_count":
            world_count,

            "simulation_pressure":
            pressure,

            "max_active_worlds":
            max_worlds,

            "budget_policy":
            (
                "strict_reality_budget"
                if pressure >= 0.75
                else "bounded_reality_budget"
            ),
        }
