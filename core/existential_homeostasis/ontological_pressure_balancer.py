def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class OntologicalPressureBalancer:

    def balance(self, context):

        graveyard = _clamp(
            context.get("evolutionary_graveyard_report", {})
            .get("graveyard_pressure", {})
            .get("pressure_score", 0.0)
        )

        resource = _clamp(
            context.get("existential_economics_report", {})
            .get("cognitive_resource_pressure", {})
            .get("pressure_score", 0.0)
        )

        pressure = _clamp(graveyard * 0.46 + resource * 0.54)

        return {
            "system": "ontological_pressure_balancer",
            "graveyard_pressure": graveyard,
            "resource_pressure": resource,
            "balanced_pressure": pressure,
            "balancer_actions": [
                "shift_from_expansion_to_repair",
                "reserve_pressure_relief_cycles",
            ]
            if pressure >= 0.42
            else [],
            "balancer_state": (
                "ontological_pressure_balancing_active"
                if pressure >= 0.42
                else "ontological_pressure_balanced"
            ),
        }
