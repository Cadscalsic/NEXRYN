def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class AdaptiveStabilityRegulator:

    def regulate(self, context):

        economics = context.get("existential_economics_report", {})
        ontology = context.get("ontological_boundary_report", {})

        total_cost = _clamp(economics.get("total_existential_cost", 0.0))
        fatigue = _clamp(
            ontology.get("existential_fatigue", {}).get(
                "ontological_fatigue",
                0.0,
            )
        )

        stability_demand = _clamp(total_cost * 0.62 + fatigue * 0.38)

        return {
            "system": "adaptive_stability_regulator",
            "total_existential_cost": total_cost,
            "ontological_fatigue": fatigue,
            "stability_demand": stability_demand,
            "regulator_actions": [
                "slow_evolutionary_expansion",
                "prioritize_stabilizing_cycles",
            ]
            if stability_demand >= 0.42
            else [],
            "regulator_state": (
                "stability_regulation_active"
                if stability_demand >= 0.42
                else "stability_regulation_standby"
            ),
        }
