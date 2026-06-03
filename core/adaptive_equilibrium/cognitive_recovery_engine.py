class CognitiveRecoveryEngine:

    def recover(self, reports):

        actions = []

        for report in reports:

            for key in [
                "planned_stability_cycles",
                "identity_core_actions",
                "semantic_actions",
                "propagation_actions",
            ]:

                actions.extend(report.get(key, []))

        if actions:

            actions.append("maintain_adaptive_equilibrium_recovery")

        return {
            "system": "cognitive_recovery_engine",
            "recovery_actions": sorted(set(actions)),
            "recovery_state": (
                "adaptive_equilibrium_recovery_active"
                if actions
                else "adaptive_equilibrium_recovery_standby"
            ),
        }
