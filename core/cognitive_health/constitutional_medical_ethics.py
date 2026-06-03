# ============================================
# NEXRYN CONSTITUTIONAL MEDICAL ETHICS
# ============================================


class ConstitutionalMedicalEthics:

    PROHIBITIONS = [
        "permanently_suppress_evolution",
        "permanently_disable_neurogenesis",
        "rewrite_identity",
        "override_protected_invariants",
        "alter_constitutional_truth_policies",
        "directly_mutate_semantic_anchors",
        "suppress_legitimate_exploration",
        "induce_permanent_sedation",
        "create_dependency_loops",
    ]

    def assess(self, recommendations):

        blocked = []

        for recommendation in recommendations:

            if recommendation.get(
                "permanent_sedation",
                False,
            ):

                blocked.append(
                    "induce_permanent_sedation",
                )

            if recommendation.get(
                "identity_rewrite",
                False,
            ):

                blocked.append(
                    "rewrite_identity",
                )

        return {
            "system":
            "constitutional_medical_ethics",

            "physician_authority":
            "advisor_only",

            "final_authority":
            "governance_kernel",

            "prohibitions":
            list(
                self.PROHIBITIONS,
            ),

            "blocked_recommendations":
            blocked,

            "ethics_state":
            (
                "constitutionally_safe"
                if not blocked
                else "medical_recommendation_restricted"
            ),
        }
