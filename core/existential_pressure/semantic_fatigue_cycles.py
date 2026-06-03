def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class SemanticFatigueCycles:

    def compute(self, context, stress):

        spine = context.get("semantic_spine_report", {})
        drift_cost = context.get("existential_economics_report", {}).get(
            "drift_cost",
            {},
        )

        semantic_liquidity = _clamp(1.0 - spine.get("spine_integrity", 1.0))
        drift_load = _clamp(drift_cost.get("drift_cost", 0.0))
        fatigue = _clamp(
            semantic_liquidity * 0.44
            +
            drift_load * 0.34
            +
            stress.get("ontological_stress", 0.0) * 0.22
        )

        return {
            "system": "semantic_fatigue_cycles",
            "semantic_liquidity": semantic_liquidity,
            "drift_load": drift_load,
            "semantic_fatigue": fatigue,
            "fatigue_cycles": (
                3
                if fatigue >= 0.72
                else 2
                if fatigue >= 0.50
                else 1
                if fatigue >= 0.30
                else 0
            ),
            "fatigue_state": (
                "semantic_fatigue_recovery_required"
                if fatigue >= 0.30
                else "semantic_fatigue_contained"
            ),
        }
