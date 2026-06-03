class OntologicalRecovery:

    def run_cycle(
        self,
        spine_report,
        identity_report,
        survival_report,
        fatigue_report,
    ):

        actions = []

        if spine_report.get(
            "fragile_semantic_spine",
            False,
        ):

            actions.extend(
                spine_report.get(
                    "controls",
                    [],
                )
            )

        if identity_report.get(
            "blocked_identity_fusions",
            0,
        ):

            actions.append(
                "route_merges_through_identity_fusion_firewall",
            )

        if survival_report.get(
            "rehabilitated_invariants",
            [],
        ):

            actions.append(
                "reactivate_dormant_critical_invariants",
            )

        if fatigue_report.get(
            "ontological_fatigue",
            0.0,
        ) >= 0.5:

            actions.append(
                "pause_large_scale_evolutionary_expansion",
            )

        return {
            "system":
            "ontological_recovery",

            "recovery_actions":
            sorted(
                set(
                    actions,
                )
            ),

            "recovery_state":
            (
                "ontological_recovery_active"
                if actions
                else "ontological_recovery_standby"
            ),
        }
