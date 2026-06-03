class FlexibleConstitutionalGovernance:

    def govern(self, context, equilibrium, abstraction):

        constitutional_freeze = context.get("freeze_new_fusions", False)
        equilibrium_score = equilibrium.get("dynamic_equilibrium", 0.0)
        abstraction_constrained = (
            abstraction.get("priority_state") == "abstraction_priority_constrained"
        )

        governance_mode = (
            "strict_constitutional_recovery"
            if constitutional_freeze or equilibrium_score < 0.46
            else "flexible_constitutional_adaptation"
            if not abstraction_constrained
            else "bounded_constitutional_adaptation"
        )

        return {
            "system": "flexible_constitutional_governance",
            "governance_mode": governance_mode,
            "governance_actions": [
                "keep_absolute_invariants_locked",
                "allow_contextual_rules_only_under_attestation",
            ]
            if governance_mode != "flexible_constitutional_adaptation"
            else [
                "allow_bounded_contextual_adaptation",
                "keep_constitutional_truths_non_negotiable",
            ],
            "governance_state": governance_mode,
        }
