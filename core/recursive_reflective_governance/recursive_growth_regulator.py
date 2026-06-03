def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class RecursiveGrowthRegulator:

    def regulate(self, reflection, topology, distributed):

        growth_pressure = _clamp(
            reflection.get("reflection_load", 0.0) * 0.36
            +
            topology.get("topology_risk", 0.0) * 0.34
            +
            distributed.get("distributed_identity_risk", 0.0) * 0.30
        )

        return {
            "system": "recursive_growth_regulator",
            "recursive_growth_pressure": growth_pressure,
            "growth_actions": [
                "cap_recursive_growth",
                "require_reflective_checkpoint_before_growth",
            ]
            if growth_pressure >= 0.38
            else [],
            "growth_state": (
                "recursive_growth_regulated"
                if growth_pressure >= 0.38
                else "recursive_growth_open_bounded"
            ),
        }
