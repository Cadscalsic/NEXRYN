# ============================================
# NEXRYN STRATEGY MUTATION ENGINE
# ============================================

import random


# ============================================
# SEMANTIC MUTATION LIMITS
# ============================================

MAX_SEMANTIC_DEPTH = 2

SEMANTIC_PREFIXES = {

    "contextual",
    "dynamic",
    "adaptive",
    "structural",
    "recursive"
}


# ============================================
# STRATEGY MUTATION ENGINE
# ============================================

class StrategyMutationEngine:

    def __init__(self):

        # ========================================
        # MUTATION RATE
        # ========================================

        self.mutation_rate = 0.25

        # ========================================
        # MUTATION PREFIXES
        # ========================================

        self.prefixes = [

            "adaptive",

            "dynamic",

            "hybrid",

            "recursive",

            "contextual"
        ]

        self.rejected_mutations = []

    # ============================================
    # SEMANTIC DEPTH
    # ============================================

    def semantic_depth(
        self,
        strategy_name
    ):

        if strategy_name is None:

            return 0

        parts = str(
            strategy_name
        ).split(
            "_"
        )

        return sum(

            1

            for part in parts

            if part in SEMANTIC_PREFIXES
        )

    # ============================================
    # SHOULD MUTATE
    # ============================================

    def should_mutate(self):

        return (

            random.random()

            <

            self.mutation_rate
        )

    # ============================================
    # MUTATE STRATEGY NAME
    # ============================================

    def mutate_name(

        self,

        strategy_name
    ):

        prefix = random.choice(
            self.prefixes
        )

        mutated_name = (

            f"{prefix}_{strategy_name}"
        )

        return mutated_name

    # ============================================
    # SHOULD REJECT MUTATION
    # ============================================

    def should_reject_mutation(
        self,
        strategy_name
    ):

        return (
            self.semantic_depth(
                strategy_name
            )
            >
            MAX_SEMANTIC_DEPTH
        )

    # ============================================
    # APPLY MUTATION
    # ============================================

    def apply_mutation(

        self,

        hypotheses
    ):

        if not hypotheses:

            return hypotheses

        mutated_hypotheses = []

        for hypothesis in hypotheses:

            mutated = dict(
                hypothesis
            )

            # ====================================
            # NO MUTATION
            # ====================================

            if not self.should_mutate():

                mutated[
                    "mutation_applied"
                ] = False

                mutated_hypotheses.append(
                    mutated
                )

                continue

            # ====================================
            # MUTATE STRATEGY
            # ====================================

            original_type = mutated.get(
                "type",
                "unknown"
            )

            mutated_type = (

                self.mutate_name(
                    original_type
                )
            )

            if self.should_reject_mutation(
                mutated_type
            ):

                mutated[
                    "mutation_applied"
                ] = False

                mutated[
                    "mutation_rejected"
                ] = True

                mutated[
                    "mutation_rejection_reason"
                ] = "semantic_depth_limit"

                self.rejected_mutations.append({

                    "original_type":
                    original_type,

                    "rejected_type":
                    mutated_type,

                    "semantic_depth":
                    self.semantic_depth(
                        mutated_type
                    )
                })

                mutated_hypotheses.append(
                    mutated
                )

                continue

            mutated[
                "parent_strategy"
            ] = original_type

            mutated[
                "type"
            ] = mutated_type

            mutated[
                "mutation_applied"
            ] = True

            mutated[
                "mutation_source"
            ] = "strategy_mutation_engine"

            mutated_hypotheses.append(
                mutated
            )

        return mutated_hypotheses
