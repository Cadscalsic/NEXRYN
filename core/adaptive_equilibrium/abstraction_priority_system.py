def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class AbstractionPrioritySystem:

    def prioritize(self, context, equilibrium):

        overhead = _clamp(
            context.get("existential_economics_report", {})
            .get("abstraction_overhead", {})
            .get("abstraction_overhead", 0.0)
        )
        dynamic_equilibrium = _clamp(equilibrium.get("dynamic_equilibrium", 0.0))

        priority = _clamp(dynamic_equilibrium * 0.64 + (1.0 - overhead) * 0.36)

        return {
            "system": "abstraction_priority_system",
            "abstraction_overhead": overhead,
            "abstraction_priority_score": priority,
            "priority_actions": [
                "defer_noncritical_abstractions",
                "prioritize_grounded_stability_abstractions",
            ]
            if priority < 0.58
            else [
                "allow_bounded_abstraction_growth",
            ],
            "priority_state": (
                "abstraction_priority_constrained"
                if priority < 0.58
                else "abstraction_priority_open_bounded"
            ),
        }
