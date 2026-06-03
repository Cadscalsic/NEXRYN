class AdaptiveSelfPreservation:

    def preserve(self, reports):

        actions = []

        for report in reports:

            for key in [
                "regulator_actions",
                "equilibrium_actions",
                "identity_actions",
                "recovery_loops",
                "balancer_actions",
                "gravity_actions",
                "planned_cycles",
            ]:

                actions.extend(report.get(key, []))

        if actions:

            actions.append("maintain_long_term_evolutionary_homeostasis")

        return {
            "system": "adaptive_self_preservation",
            "self_preservation_actions": sorted(set(actions)),
            "self_preservation_state": (
                "adaptive_self_preservation_active"
                if actions
                else "adaptive_self_preservation_standby"
            ),
        }
