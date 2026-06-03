def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(value, maximum),
        ),
        4,
    )


class SemanticSpineProtectionEngine:

    def run_cycle(self, context):

        spine = context.get(
            "semantic_spine_report",
            {},
        )

        spine_stability = _clamp(
            spine.get(
                "spine_integrity",
                0.0,
            )
        )

        fragile = (
            spine_stability < 0.56
            or spine.get(
                "semantic_spine_state",
            )
            in [
                "fragile_semantic_spine",
                "semantic_spine_repairing",
            ]
        )

        controls = []

        if fragile:

            controls = [
                "reduce_merge_pressure",
                "freeze_high_risk_mutations",
                "reinforce_identity_anchors",
                "increase_temporal_validation",
            ]

        return {
            "system":
            "semantic_spine_protection",

            "spine_stability":
            spine_stability,

            "fragile_semantic_spine":
            fragile,

            "controls":
            controls,

            "protection_state":
            (
                "semantic_spine_under_ontological_protection"
                if fragile
                else "semantic_spine_within_safe_bounds"
            ),
        }
