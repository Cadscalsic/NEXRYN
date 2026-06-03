def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class DriftCostTracker:

    def compute(self, context):

        stability = context.get(
            "stability_field_report",
            {},
        ).get(
            "semantic_drift",
            {},
        )

        drift = _clamp(
            stability.get(
                "semantic_drift",
                context.get(
                    "semantic_drift",
                    0.0,
                ),
            )
        )

        clusters = context.get(
            "identity_continuity_guardian_report",
            {},
        ).get(
            "drift_clusters",
            {},
        ).get(
            "drift_cluster_count",
            0,
        )

        cost = _clamp(
            drift * 0.70
            +
            clusters * 0.08
        )

        return {
            "system":
            "drift_cost_tracker",

            "semantic_drift":
            drift,

            "drift_cluster_count":
            clusters,

            "drift_cost":
            cost,

            "cost_state":
            (
                "drift_cost_high"
                if cost >= 0.58
                else "drift_cost_elevated"
                if cost >= 0.32
                else "drift_cost_contained"
            ),
        }
