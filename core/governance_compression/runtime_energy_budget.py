# ============================================
# NEXRYN RUNTIME ENERGY BUDGET
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


class RuntimeEnergyBudget:

    BASE_COSTS = {
        "governance_kernel": (0.08, 0.05, 0.06),
        "epistemic_constitution": (0.10, 0.09, 0.07),
        "cognitive_physician": (0.10, 0.08, 0.05),
        "semantic_compression": (0.10, 0.08, 0.04),
        "cognitive_kernel": (0.12, 0.08, 0.08),
        "semantic_os": (0.16, 0.12, 0.06),
        "concept_lifecycle": (0.10, 0.10, 0.04),
        "cognitive_physics": (0.18, 0.14, 0.06),
        "reasoning": (0.24, 0.18, 0.04),
        "legacy_governance_aliases": (0.02, 0.02, 0.02),
    }

    def compute_pressure(self, context):

        kernel = context.get(
            "cognitive_kernel_report",
            {},
        )

        pressure = kernel.get(
            "pressure_report",
            {},
        ).get(
            "total_kernel_pressure",
            context.get(
                "runtime_entropy",
                0.0,
            ),
        )

        return _clamp(
            pressure,
        )

    def allocate(self, context, active_modules):

        pressure = self.compute_pressure(
            context,
        )

        budgets = {}

        for subsystem in active_modules:

            energy_cost, attention_cost, governance_cost = (
                self.BASE_COSTS.get(
                    subsystem,
                    (0.12, 0.08, 0.04),
                )
            )

            memory_cost = _clamp(
                energy_cost * 0.70
                +
                pressure * 0.10
            )

            budgets[
                subsystem
            ] = {
                "energy_budget":
                _clamp(
                    max(
                        0.02,
                        0.22 - energy_cost - pressure * 0.04,
                    )
                ),

                "attention_cost":
                _clamp(
                    attention_cost
                    +
                    pressure * 0.04
                ),

                "memory_cost":
                memory_cost,

                "governance_cost":
                _clamp(
                    governance_cost
                    +
                    pressure * 0.03
                ),
            }

        total_governance_cost = _clamp(
            sum(
                item.get(
                    "governance_cost",
                    0.0,
                )
                for item in budgets.values()
            )
        )

        return {
            "system":
            "runtime_energy_budget",

            "pressure":
            pressure,

            "subsystems":
            budgets,

            "total_governance_cost":
            total_governance_cost,

            "budget_state":
            (
                "governance_over_budget"
                if total_governance_cost >= 0.70
                else "within_budget"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
