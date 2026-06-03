def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class PressureAccumulationEngine:

    def accumulate(self, context):

        economics = context.get("existential_economics_report", {})
        homeostasis = context.get("existential_homeostasis_report", {})

        economic_pressure = _clamp(
            economics.get("cognitive_resource_pressure", {}).get(
                "pressure_score",
                0.0,
            )
        )
        existential_cost = _clamp(economics.get("total_existential_cost", 0.0))
        homeostasis_gap = _clamp(
            1.0
            -
            homeostasis.get(
                "existential_homeostasis_score",
                1.0,
            )
        )
        graveyard_pressure = _clamp(
            context.get("evolutionary_graveyard_report", {})
            .get("graveyard_pressure", {})
            .get("pressure_score", 0.0)
        )
        memory_pressure = _clamp(context.get("memory_pressure_score", 0.0))

        accumulated_pressure = _clamp(
            economic_pressure * 0.24
            +
            existential_cost * 0.24
            +
            homeostasis_gap * 0.20
            +
            graveyard_pressure * 0.18
            +
            memory_pressure * 0.14
        )

        return {
            "system": "pressure_accumulation_engine",
            "economic_pressure": economic_pressure,
            "existential_cost": existential_cost,
            "homeostasis_gap": homeostasis_gap,
            "graveyard_pressure": graveyard_pressure,
            "memory_pressure": memory_pressure,
            "accumulated_pressure": accumulated_pressure,
            "pressure_state": (
                "existential_pressure_critical"
                if accumulated_pressure >= 0.72
                else "existential_pressure_high"
                if accumulated_pressure >= 0.50
                else "existential_pressure_elevated"
                if accumulated_pressure >= 0.30
                else "existential_pressure_contained"
            ),
        }
