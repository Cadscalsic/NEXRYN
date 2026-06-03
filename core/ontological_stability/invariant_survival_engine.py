class InvariantSurvivalEngine:

    CRITICAL_INVARIANTS = {
        "topology_preservation",
        "symmetry_preservation",
        "size_preservation",
    }

    def run_cycle(self, context):

        extinct = context.get(
            "extinction_engine_report",
            {},
        ).get(
            "extinct_traits",
            [],
        )

        rehabilitated = []

        for trait in extinct:

            trait_id = trait.get(
                "id",
                trait.get(
                    "trait_id",
                    trait.get(
                        "trait_name",
                    ),
                ),
            )

            if trait_id in self.CRITICAL_INVARIANTS:

                rehabilitated.append({
                    "invariant_id":
                    trait_id,

                    "rehabilitation_action":
                    "preserve_as_dormant_with_contextual_reactivation",
                })

        return {
            "system":
            "invariant_survival_engine",

            "rehabilitated_invariants":
            rehabilitated,

            "survival_state":
            (
                "critical_invariants_rehabilitated"
                if rehabilitated
                else "no_extinct_critical_invariants"
            ),
        }
