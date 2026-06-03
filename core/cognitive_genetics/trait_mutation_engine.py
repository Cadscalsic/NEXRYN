# ============================================
# NEXRYN TRAIT MUTATION ENGINE
# ============================================


class TraitMutationEngine:

    def propose(self, traits, context):

        pressure = context.get(
            "semantic_entropy",
            context.get(
                "runtime_entropy",
                0.0,
            ),
        )

        proposed = []

        if pressure >= 0.68:

            proposed.append({
                "category": "balancing_adjustment",
                "target_trait": "SEMANTIC_BALANCE",
                "intent": "increase_grounding_under_entropy_pressure",
            })

        if context.get(
            "exploration_suppression_rate",
            0.0,
        ) >= 0.58:

            proposed.append({
                "category": "curiosity_modulation",
                "target_trait": "BOUNDED_CURIOSITY",
                "intent": "restore_safe_exploration",
            })

        return {
            "system": "trait_mutation_engine",
            "proposed_mutations": proposed,
            "mutation_authority": "sandboxed_rehearsal_only",
        }
