def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class RecursiveReflectionEngine:

    def reflect(self, context):

        recursive_paths = context.get(
            "recursive_paths",
            context.get(
                "recursive_governance_report",
                {},
            ).get(
                "recursive_paths",
                [],
            ),
        )

        if not isinstance(recursive_paths, list):

            recursive_paths = []

        pressure = _clamp(
            context.get("existential_pressure_report", {})
            .get("managed_pressure", 0.0)
        )

        reflection_load = _clamp(
            len(recursive_paths) * 0.08
            +
            pressure * 0.34
        )

        return {
            "system": "recursive_reflection_engine",
            "recursive_path_count": len(recursive_paths),
            "managed_pressure": pressure,
            "reflection_load": reflection_load,
            "reflection_actions": [
                "reflect_before_recursive_expansion",
                "summarize_recursive_state_before_propagation",
            ]
            if reflection_load >= 0.34
            else [],
            "reflection_state": (
                "recursive_reflection_active"
                if reflection_load >= 0.34
                else "recursive_reflection_standby"
            ),
        }
