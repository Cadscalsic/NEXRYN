def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class OntologicalStressMonitor:

    def monitor(self, context, accumulation):

        fatigue = _clamp(
            context.get("ontological_boundary_report", {})
            .get("existential_fatigue", {})
            .get("ontological_fatigue", 0.0)
        )
        tension = _clamp(accumulation.get("accumulated_pressure", 0.0))
        blocked = context.get("ontological_boundary_report", {}).get(
            "identity_boundary",
            {},
        ).get("blocked_identity_fusions", 0)

        stress = _clamp(fatigue * 0.46 + tension * 0.42 + blocked * 0.08)

        return {
            "system": "ontological_stress_monitor",
            "ontological_fatigue": fatigue,
            "blocked_identity_fusions": blocked,
            "ontological_stress": stress,
            "stress_state": (
                "ontological_stress_critical"
                if stress >= 0.72
                else "ontological_stress_high"
                if stress >= 0.50
                else "ontological_stress_elevated"
                if stress >= 0.30
                else "ontological_stress_contained"
            ),
        }
