def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(minimum, min(value, maximum)),
        4,
    )


class IdentityCostEngine:

    def compute(self, context):

        continuity = _clamp(
            context.get(
                "identity_continuity",
                context.get(
                    "identity_continuity_guardian_report",
                    {},
                ).get(
                    "identity_continuity",
                    context.get(
                        "identity_continuity_guardian_report",
                        {},
                    ).get(
                        "continuity_score",
                        0.5,
                    ),
                ),
            )
        )

        boundary = context.get(
            "ontological_boundary_report",
            {},
        ).get(
            "identity_boundary",
            {},
        )

        blocked_fusions = boundary.get(
            "blocked_identity_fusions",
            0,
        )

        fatigue = context.get(
            "ontological_boundary_report",
            {},
        ).get(
            "existential_fatigue",
            {},
        )

        cost = _clamp(
            (1.0 - continuity) * 0.45
            +
            blocked_fusions * 0.16
            +
            fatigue.get(
                "identity_stress",
                0.0,
            )
            * 0.30
        )

        return {
            "system":
            "identity_cost_engine",

            "identity_continuity":
            continuity,

            "blocked_identity_fusions":
            blocked_fusions,

            "identity_maintenance_cost":
            cost,

            "cost_state":
            (
                "identity_cost_high"
                if cost >= 0.58
                else "identity_cost_elevated"
                if cost >= 0.32
                else "identity_cost_contained"
            ),
        }
