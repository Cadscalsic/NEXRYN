# ============================================
# NEXRYN KERNEL BUDGET
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


class KernelBudget:

    def compute_pressure(self, context):

        memory_pressure = context.get(
            "working_memory_pressure",
            context.get(
                "governance_report",
                {},
            ).get(
                "memory_pressure",
                0.0,
            ),
        )

        attention = context.get(
            "dynamic_attention_allocation",
            {},
        ).get(
            "attention_saturation",
            context.get(
                "attention_saturation",
                0.0,
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

        overload = context.get(
            "projected_overload",
            context.get(
                "predictive_collapse_report",
                {},
            ).get(
                "projected_overload",
                0.0,
            ),
        )

        energy_state = context.get(
            "energy_state",
            context.get(
                "cognitive_energy_economy_report",
                {},
            ).get(
                "energy_state",
                "balanced",
            ),
        )

        energy_pressure = (
            1.0
            if energy_state == "critical"
            else 0.72
            if energy_state == "constrained"
            else 0.35
        )

        total_pressure = _clamp(
            memory_pressure * 0.25
            +
            attention * 0.20
            +
            entropy * 0.22
            +
            overload * 0.18
            +
            energy_pressure * 0.15
        )

        return {
            "working_memory_pressure":
            _clamp(
                memory_pressure,
            ),

            "attention_saturation":
            _clamp(
                attention,
            ),

            "runtime_entropy":
            _clamp(
                entropy,
            ),

            "projected_overload":
            _clamp(
                overload,
            ),

            "energy_state":
            energy_state,

            "total_kernel_pressure":
            total_pressure,
        }

    def allocate(self, mode, pressure_report):

        pressure = pressure_report.get(
            "total_kernel_pressure",
            0.0,
        )

        if mode == "stabilization_mode":

            return {
                "reasoning":
                0.0,

                "stabilization":
                _clamp(
                    0.70 + pressure * 0.20,
                ),

                "exploration":
                0.0,

                "memory":
                _clamp(
                    0.55 + pressure * 0.20,
                ),

                "meta_control":
                _clamp(
                    0.22,
                ),
            }

        if mode == "exploration_mode":

            return {
                "reasoning":
                0.30,

                "stabilization":
                0.25,

                "exploration":
                _clamp(
                    0.35 - pressure * 0.12,
                ),

                "memory":
                0.22,

                "meta_control":
                0.18,
            }

        return {
            "reasoning":
            _clamp(
                0.48 - pressure * 0.12,
            ),

            "stabilization":
            _clamp(
                0.28 + pressure * 0.08,
            ),

            "exploration":
            _clamp(
                0.12 - pressure * 0.08,
            ),

            "memory":
            0.30,

            "meta_control":
            0.16,
        }
