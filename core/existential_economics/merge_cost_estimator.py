def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class MergeCostEstimator:

    def compute(self, context):

        fusion = context.get(
            "concept_fusion_report",
            {},
        )

        rejected = fusion.get(
            "rejected_count",
            len(
                fusion.get(
                    "rejected_fusions",
                    [],
                )
            ),
        )

        blocked_identity = context.get(
            "ontological_boundary_report",
            {},
        ).get(
            "identity_boundary",
            {},
        ).get(
            "blocked_identity_fusions",
            0,
        )

        pressure = context.get(
            "evolutionary_graveyard_report",
            {},
        ).get(
            "graveyard_pressure",
            {},
        ).get(
            "pressure_score",
            0.0,
        )

        cost = _clamp(
            rejected * 0.11
            +
            blocked_identity * 0.18
            +
            pressure * 0.22
        )

        return {
            "system":
            "merge_cost_estimator",

            "rejected_merges":
            rejected,

            "blocked_identity_fusions":
            blocked_identity,

            "graveyard_pressure":
            pressure,

            "merge_cost":
            cost,

            "cost_state":
            (
                "merge_cost_high"
                if cost >= 0.58
                else "merge_cost_elevated"
                if cost >= 0.32
                else "merge_cost_contained"
            ),
        }
