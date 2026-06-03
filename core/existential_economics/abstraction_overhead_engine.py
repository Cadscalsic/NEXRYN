def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class AbstractionOverheadEngine:

    def compute(self, context):

        stability = context.get(
            "stability_field_report",
            {},
        ).get(
            "cognitive_pressure",
            {},
        )

        abstraction_overload = _clamp(
            stability.get(
                "abstraction_overload",
                0.0,
            )
        )

        semantic_abstractions = context.get(
            "semantic_abstractions",
            [],
        )

        count = (
            len(semantic_abstractions)
            if isinstance(semantic_abstractions, list)
            else 0
        )

        overhead = _clamp(
            abstraction_overload * 0.65
            +
            count * 0.025
        )

        return {
            "system":
            "abstraction_overhead_engine",

            "abstraction_count":
            count,

            "abstraction_overload":
            abstraction_overload,

            "abstraction_overhead":
            overhead,

            "overhead_state":
            (
                "abstraction_overhead_high"
                if overhead >= 0.58
                else "abstraction_overhead_elevated"
                if overhead >= 0.32
                else "abstraction_overhead_contained"
            ),
        }
