class ExistentialHomeostasis:

    def compute(self, pressure, allocator):

        score = pressure.get(
            "pressure_score",
            0.0,
        )

        actions = []

        if score >= 0.28:

            actions.append(
                "price_identity_preservation_before_new_evolution",
            )

        if score >= 0.48:

            actions.extend([
                "reduce_merge_frequency",
                "defer_noncritical_abstractions",
                "prioritize_continuity_budget",
            ])

        if score >= 0.72:

            actions.append(
                "enter_existential_budget_emergency_mode",
            )

        if allocator.get(
            "allocator_state",
        ) == "continuity_prioritized":

            actions.append(
                "reserve_resources_for_identity_continuity",
            )

        return {
            "system":
            "existential_homeostasis",

            "homeostasis_actions":
            sorted(
                set(actions),
            ),

            "homeostasis_state":
            (
                "existential_homeostasis_intervention"
                if actions
                else "existential_homeostasis_balanced"
            ),
        }
