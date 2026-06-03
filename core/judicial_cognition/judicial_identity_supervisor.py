class JudicialIdentitySupervisor:

    def supervise(self, reports):

        actions = []

        for report in reports:

            for key in [
                "court_actions",
                "ambiguity_actions",
                "sandbox_actions",
                "topology_judgement_actions",
                "legality_actions",
                "causal_actions",
                "gatekeeper_actions",
                "admissibility_actions",
            ]:

                actions.extend(report.get(key, []))

        return {
            "system": "judicial_identity_supervisor",
            "judicial_actions": sorted(set(actions)),
            "judicial_identity_state": (
                "judicial_identity_supervision_active"
                if actions
                else "judicial_identity_supervision_clear"
            ),
        }
