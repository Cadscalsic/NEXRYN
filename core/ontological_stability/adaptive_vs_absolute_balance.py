class AdaptiveVsAbsoluteBalance:

    def run_cycle(self, invariant_report, negotiation_report):

        hierarchy = invariant_report.get(
            "invariant_hierarchy",
            [],
        )

        negotiable = len([
            item
            for item in hierarchy
            if item.get(
                "negotiable",
            )
        ])

        absolute = len(
            hierarchy
        ) - negotiable

        blocked = len(
            negotiation_report.get(
                "blocked_negotiations",
                [],
            )
        )

        return {
            "system":
            "adaptive_vs_absolute_balance",

            "absolute_invariants":
            absolute,

            "adaptive_invariants":
            negotiable,

            "blocked_contextual_negotiations":
            blocked,

            "balance_state":
            (
                "absolute_boundaries_preserved"
                if absolute >= negotiable
                else "adaptation_pressure_requires_boundary_review"
            ),
        }
