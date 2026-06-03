def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class InvariantCostModel:

    def compute(self, context):

        boundary = context.get(
            "ontological_boundary_report",
            {},
        ).get(
            "invariant_boundary",
            {},
        )

        protected = boundary.get(
            "protected_invariants",
            [],
        )

        rehabilitated = context.get(
            "ontological_boundary_report",
            {},
        ).get(
            "invariant_survival",
            {},
        ).get(
            "rehabilitated_invariants",
            [],
        )

        cost = _clamp(
            len(protected) * 0.035
            +
            len(rehabilitated) * 0.12
        )

        return {
            "system":
            "invariant_cost_model",

            "protected_invariant_count":
            len(protected),

            "rehabilitated_invariant_count":
            len(rehabilitated),

            "invariant_preservation_cost":
            cost,

            "cost_state":
            (
                "invariant_cost_high"
                if cost >= 0.58
                else "invariant_cost_elevated"
                if cost >= 0.32
                else "invariant_cost_contained"
            ),
        }
