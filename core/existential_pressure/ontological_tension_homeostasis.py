class OntologicalTensionHomeostasis:

    def balance(self, reports):

        actions = []

        for report in reports:

            for key in [
                "damping_actions",
                "release_actions",
                "merge_actions",
                "absorption_actions",
                "resonance_actions",
                "strain_actions",
            ]:

                actions.extend(report.get(key, []))

        return {
            "system": "ontological_tension_homeostasis",
            "tension_actions": sorted(set(actions)),
            "tension_homeostasis_state": (
                "ontological_tension_homeostasis_active"
                if actions
                else "ontological_tension_homeostasis_balanced"
            ),
        }
