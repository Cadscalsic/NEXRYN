def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticGravityEngine:

    def compute(self, context, semantic_equilibrium):

        gravity = context.get("semantic_spine_report", {}).get(
            "semantic_gravity",
            {},
        )

        gravity_strength = _clamp(gravity.get("gravity_strength", 0.0))
        equilibrium_gap = _clamp(
            1.0 - semantic_equilibrium.get("semantic_equilibrium", 0.0)
        )
        required_gravity = _clamp(gravity_strength + equilibrium_gap * 0.36)

        return {
            "system": "semantic_gravity_engine",
            "current_gravity": gravity_strength,
            "required_gravity": required_gravity,
            "gravity_actions": [
                "strengthen_anchor_attractor_fields",
                "increase_semantic_mass_around_core_invariants",
            ]
            if required_gravity > gravity_strength
            else [],
            "gravity_state": (
                "semantic_gravity_reinforcement_required"
                if required_gravity > gravity_strength
                else "semantic_gravity_sufficient"
            ),
        }
