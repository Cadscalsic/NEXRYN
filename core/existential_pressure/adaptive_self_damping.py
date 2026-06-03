def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class AdaptiveSelfDamping:

    def damp(self, accumulation, stress, fatigue):

        damping_strength = _clamp(
            accumulation.get("accumulated_pressure", 0.0) * 0.42
            +
            stress.get("ontological_stress", 0.0) * 0.34
            +
            fatigue.get("semantic_fatigue", 0.0) * 0.24
        )

        return {
            "system": "adaptive_self_damping",
            "damping_strength": damping_strength,
            "damping_actions": [
                "reduce_recursive_intensity",
                "slow_contextual_reinterpretation",
                "lower_nonessential_mutation_rate",
            ]
            if damping_strength >= 0.36
            else [],
            "damping_state": (
                "adaptive_self_damping_active"
                if damping_strength >= 0.36
                else "adaptive_self_damping_standby"
            ),
        }
