class RecursiveStabilitySupervisor:

    def supervise(self, reports):

        actions = []

        for report in reports:

            for key in [
                "reflection_actions",
                "monitor_actions",
                "identity_actions",
                "growth_actions",
                "pruning_actions",
                "limit_actions",
                "prediction_actions",
                "diffusion_actions",
            ]:

                actions.extend(report.get(key, []))

        return {
            "system": "recursive_stability_supervisor",
            "supervisor_actions": sorted(set(actions)),
            "supervisor_state": (
                "recursive_stability_supervision_active"
                if actions
                else "recursive_stability_supervision_standby"
            ),
        }
