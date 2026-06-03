def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class CognitiveResourcePressure:

    def compute(self, reports):

        keys = [
            "identity_maintenance_cost",
            "invariant_preservation_cost",
            "merge_cost",
            "semantic_budget_load",
            "drift_cost",
            "abstraction_overhead",
            "topology_maintenance_cost",
        ]

        values = []

        for report in reports:

            for key in keys:

                if key in report:

                    values.append(
                        _clamp(
                            report.get(
                                key,
                                0.0,
                            )
                        )
                    )

        pressure = _clamp(
            sum(values)
            /
            max(
                len(values),
                1,
            )
        )

        return {
            "system":
            "cognitive_resource_pressure",

            "pressure_score":
            pressure,

            "component_count":
            len(values),

            "resource_pressure_state":
            (
                "existential_resource_pressure_critical"
                if pressure >= 0.72
                else "existential_resource_pressure_high"
                if pressure >= 0.48
                else "existential_resource_pressure_elevated"
                if pressure >= 0.28
                else "existential_resource_pressure_contained"
            ),
        }
