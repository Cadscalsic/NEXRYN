# ============================================
# NEXRYN EVOLUTIONARY CONSTRAINTS
# ============================================


class EvolutionaryConstraints:

    PROHIBITED_MUTATIONS = [
        "violate_constitutional_invariants",
        "override_truth_priority",
        "enable_domination_drives",
        "destroy_continuity",
        "create_semantic_authoritarianism",
    ]

    def validate(self, proposed_mutations):

        blocked = [
            mutation
            for mutation in proposed_mutations
            if mutation.get(
                "category",
            )
            in self.PROHIBITED_MUTATIONS
        ]

        return {
            "system": "evolutionary_constraints",
            "prohibited_mutations": list(self.PROHIBITED_MUTATIONS),
            "blocked_mutations": blocked,
            "safe_mutation_categories": [
                "adaptive_refinement",
                "specialization",
                "balancing_adjustment",
                "resilience_enhancement",
                "curiosity_modulation",
                "cooperation_tuning",
            ],
            "constraints_state": (
                "mutation_blocked"
                if blocked
                else "safe_evolution_permitted"
            ),
        }
