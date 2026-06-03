def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ResonanceStabilityControl:

    def control(self, accumulation, semantic_fatigue, merge_pressure):

        resonance_risk = _clamp(
            accumulation.get("accumulated_pressure", 0.0) * 0.36
            +
            semantic_fatigue.get("semantic_fatigue", 0.0) * 0.32
            +
            merge_pressure.get("merge_pressure", 0.0) * 0.32
        )

        return {
            "system": "resonance_stability_control",
            "resonance_risk": resonance_risk,
            "resonance_actions": [
                "desynchronize_merge_and_drift_cycles",
                "stabilize_semantic_resonance",
            ]
            if resonance_risk >= 0.40
            else [],
            "resonance_state": (
                "resonance_stability_control_active"
                if resonance_risk >= 0.40
                else "resonance_stability_control_standby"
            ),
        }
