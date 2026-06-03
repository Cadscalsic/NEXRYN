def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class DynamicEquilibriumEngine:

    def compute(self, context):

        pressure = context.get("existential_pressure_report", {})
        homeostasis = context.get("existential_homeostasis_report", {})

        managed_pressure = _clamp(pressure.get("managed_pressure", 0.0))
        homeostasis_score = _clamp(
            homeostasis.get("existential_homeostasis_score", 0.5)
        )
        semantic_equilibrium = _clamp(
            homeostasis.get("semantic_equilibrium", {}).get(
                "semantic_equilibrium",
                0.5,
            )
        )
        continuity = _clamp(
            homeostasis.get("continuity_equilibrium", {}).get(
                "continuity_equilibrium",
                0.5,
            )
        )

        equilibrium = _clamp(
            (1.0 - managed_pressure) * 0.30
            +
            homeostasis_score * 0.28
            +
            semantic_equilibrium * 0.22
            +
            continuity * 0.20
        )

        return {
            "system": "dynamic_equilibrium_engine",
            "managed_pressure": managed_pressure,
            "homeostasis_score": homeostasis_score,
            "semantic_equilibrium": semantic_equilibrium,
            "continuity_equilibrium": continuity,
            "dynamic_equilibrium": equilibrium,
            "equilibrium_state": (
                "adaptive_equilibrium_strained"
                if equilibrium < 0.46
                else "adaptive_equilibrium_balancing"
                if equilibrium < 0.66
                else "adaptive_equilibrium_stable"
            ),
        }
