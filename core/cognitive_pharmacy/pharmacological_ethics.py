# ============================================
# NEXRYN COGNITIVE PHARMACY ETHICS
# ============================================


class PharmacologicalEthics:

    RULES = [
        "truth_precedes_survival_claims",
        "bounded_stabilization",
        "adaptive_freedom_preservation",
        "constitutional_cognition",
        "temporary_intervention_preference",
        "minimum_necessary_regulation",
        "cognitive_dignity_preservation",
    ]

    PROHIBITIONS = [
        "rewrite_identity",
        "override_protected_invariants",
        "permanently_disable_neurogenesis",
        "permanently_suppress_exploration",
        "alter_constitutional_truth_rules",
        "bypass_governance_kernel",
        "directly_commit_ontology_mutations",
        "modify_semantic_anchors_without_authorization",
    ]

    def validate(self, administrations, governance_review):

        approved = governance_review.get(
            "approved_for_controlled_execution",
            False,
        )

        return {
            "system": "pharmacological_ethics",
            "rules": list(
                self.RULES,
            ),
            "prohibitions": list(
                self.PROHIBITIONS,
            ),
            "governance_approved": approved,
            "pharmacy_can_act_independently": False,
            "constitutional_state": (
                "administration_constitutionally_bounded"
                if approved
                else "administration_blocked_pending_governance"
            ),
            "blocked_administrations": (
                []
                if approved
                else [
                    item.get(
                        "medication_id",
                    )
                    for item in administrations
                ]
            ),
        }
