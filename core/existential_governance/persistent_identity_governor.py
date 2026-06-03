class PersistentIdentityGovernor:

    def govern(self, reports):

        actions = []

        for report in reports:

            for key in [
                "validation_actions",
                "resolver_actions",
                "legitimacy_actions",
                "memory_actions",
                "reasoning_actions",
                "drift_actions",
                "ethics_actions",
                "graph_actions",
                "judgement_actions",
            ]:

                actions.extend(report.get(key, []))

        return {
            "system": "persistent_identity_governor",
            "identity_governance_actions": sorted(set(actions)),
            "identity_governance_state": (
                "persistent_identity_governance_active"
                if actions
                else "persistent_identity_governance_clear"
            ),
        }
