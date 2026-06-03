# ============================================
# NEXRYN EVOLUTION SIMULATION SANDBOX
# ============================================

from datetime import datetime


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(
                value,
                maximum,
            ),
        ),
        4,
    )


class EvolutionSimulationSandbox:

    def __init__(self):

        self.sandbox_history = []

    def _traits(self, context):

        recovered = context.get(
            "trait_recovery_report",
            {},
        ).get(
            "recovered_traits",
            [],
        )

        selected = context.get(
            "cognitive_natural_selection_report",
            {},
        ).get(
            "selected_traits",
            [],
        )

        traits = recovered + selected

        if traits:

            return traits

        return (
            context.get(
                "evolutionary_memory_report",
                {},
            )
            .get(
                "adaptive_trait_memory",
                {},
            )
            .get(
                "traits",
                [],
            )
        )

    def _entropy(self, context):

        return _clamp(
            context.get(
                "runtime_entropy",
                context.get(
                    "entropy_regulator_report",
                    {},
                ).get(
                    "entropy_delta_report",
                    {},
                ).get(
                    "runtime_entropy",
                    0.0,
                ),
            )
        )

    def _identity_continuity(self, context):

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        return _clamp(
            guardian.get(
                "state_transition",
                {},
            ).get(
                "current_state",
                {},
            ).get(
                "identity_continuity",
                context.get(
                    "identity_continuity",
                    0.0,
                ),
            )
        )

    def simulated_mutation_branches(self, traits, context):

        entropy = self._entropy(
            context,
        )

        cooling_factor = _clamp(
            context.get(
                "entropy_regulator_report",
                {},
            ).get(
                "cognitive_cooling",
                {},
            ).get(
                "cooling_factor",
                1.0,
            )
        )

        branch_profiles = [
            {
                "branch_id":
                "conservative_stabilization",

                "mutation_multiplier":
                0.38,

                "novelty_multiplier":
                0.42,
            },
            {
                "branch_id":
                "balanced_adaptation",

                "mutation_multiplier":
                0.72,

                "novelty_multiplier":
                0.70,
            },
            {
                "branch_id":
                "exploratory_growth",

                "mutation_multiplier":
                1.18,

                "novelty_multiplier":
                1.12,
            },
        ]

        branches = []

        for profile in branch_profiles:

            mutated_traits = []

            for trait in traits:

                trait_id = trait.get(
                    "id",
                    trait.get(
                        "trait_id",
                        trait.get(
                            "trait",
                            "unknown",
                        ),
                    ),
                )

                base_rate = _clamp(
                    trait.get(
                        "mutation_rate",
                        0.10,
                    )
                )

                simulated_rate = _clamp(
                    base_rate
                    *
                    profile.get(
                        "mutation_multiplier",
                        1.0,
                    )
                    *
                    max(
                        cooling_factor,
                        0.08,
                    )
                )

                projected_fitness = _clamp(
                    trait.get(
                        "fitness",
                        trait.get(
                            "net_fitness",
                            0.0,
                        ),
                    )
                    +
                    profile.get(
                        "novelty_multiplier",
                        1.0,
                    )
                    * 0.08
                    -
                    entropy
                    * simulated_rate
                    * 0.42
                )

                mutated_traits.append({
                    "trait_id":
                    trait_id,

                    "base_mutation_rate":
                    base_rate,

                    "simulated_mutation_rate":
                    simulated_rate,

                    "projected_fitness":
                    projected_fitness,

                    "trait_state":
                    trait.get(
                        "trait_state",
                        "candidate",
                    ),
                })

            branches.append({
                "branch_id":
                profile.get(
                    "branch_id",
                    "unknown_branch",
                ),

                "mutation_multiplier":
                profile.get(
                    "mutation_multiplier",
                    1.0,
                ),

                "novelty_multiplier":
                profile.get(
                    "novelty_multiplier",
                    1.0,
                ),

                "mutated_traits":
                mutated_traits,
            })

        return branches

    def evolutionary_forecasting(self, branch, context):

        traits = branch.get(
            "mutated_traits",
            [],
        )

        identity = self._identity_continuity(
            context,
        )

        entropy = self._entropy(
            context,
        )

        average_mutation = _clamp(
            sum(
                trait.get(
                    "simulated_mutation_rate",
                    0.0,
                )
                for trait in traits
            )
            /
            max(
                len(
                    traits,
                ),
                1,
            )
        )

        average_fitness = _clamp(
            sum(
                trait.get(
                    "projected_fitness",
                    0.0,
                )
                for trait in traits
            )
            /
            max(
                len(
                    traits,
                ),
                1,
            )
        )

        adaptive_gain = _clamp(
            average_fitness
            * 0.58
            +
            branch.get(
                "novelty_multiplier",
                1.0,
            )
            * 0.12
            -
            entropy
            * average_mutation
            * 0.30
        )

        identity_cost = _clamp(
            average_mutation
            * 0.52
            +
            (
                1.0
                -
                identity
            )
            * 0.48
        )

        return {
            "branch_id":
            branch.get(
                "branch_id",
                "unknown_branch",
            ),

            "average_mutation_rate":
            average_mutation,

            "average_projected_fitness":
            average_fitness,

            "adaptive_gain":
            adaptive_gain,

            "identity_cost":
            identity_cost,

            "forecast_state":
            (
                "promising_future"
                if adaptive_gain >= 0.46
                and identity_cost < 0.42
                else "risky_future"
                if identity_cost >= 0.42
                else "neutral_future"
            ),
        }

    def collapse_prediction(self, forecast, context):

        guardian = context.get(
            "identity_continuity_guardian_report",
            {},
        )

        rewrite_blocked = guardian.get(
            "catastrophic_rewrite_guard",
            {},
        ).get(
            "block_rewrite",
            False,
        )

        storm_pressure = _clamp(
            context.get(
                "entropy_regulator_report",
                {},
            ).get(
                "mutation_storm_control",
                {},
            ).get(
                "storm_pressure",
                0.0,
            )
        )

        collapse_risk = _clamp(
            forecast.get(
                "identity_cost",
                0.0,
            )
            * 0.42
            +
            storm_pressure
            * 0.28
            +
            (
                0.30
                if rewrite_blocked
                else 0.0
            )
            +
            (
                1.0
                -
                forecast.get(
                    "adaptive_gain",
                    0.0,
                )
            )
            * 0.18
        )

        return {
            "branch_id":
            forecast.get(
                "branch_id",
                "unknown_branch",
            ),

            "collapse_risk":
            collapse_risk,

            "collapse_state":
            (
                "collapse_predicted"
                if collapse_risk >= 0.64
                else "collapse_watch"
                if collapse_risk >= 0.42
                else "collapse_unlikely"
            ),
        }

    def parallel_futures(self, branches, context):

        futures = []

        for branch in branches:

            forecast = self.evolutionary_forecasting(
                branch,
                context,
            )

            collapse = self.collapse_prediction(
                forecast,
                context,
            )

            commit_probability = _clamp(
                forecast.get(
                    "adaptive_gain",
                    0.0,
                )
                * 0.62
                +
                (
                    1.0
                    -
                    collapse.get(
                        "collapse_risk",
                        0.0,
                    )
                )
                * 0.38
            )

            futures.append({
                "branch_id":
                branch.get(
                    "branch_id",
                    "unknown_branch",
                ),

                "branch":
                branch,

                "forecast":
                forecast,

                "collapse_prediction":
                collapse,

                "commit_probability":
                commit_probability,

                "sandbox_decision":
                (
                    "candidate_for_commit"
                    if commit_probability >= 0.58
                    and collapse.get(
                        "collapse_state",
                    )
                    == "collapse_unlikely"
                    else "continue_rehearsal"
                    if commit_probability >= 0.38
                    else "reject_branch"
                ),
            })

        return futures

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        traits = self._traits(
            context,
        )

        branches = self.simulated_mutation_branches(
            traits,
            context,
        )

        futures = self.parallel_futures(
            branches,
            context,
        )

        candidate_futures = [
            future
            for future in futures
            if future.get(
                "sandbox_decision",
            )
            == "candidate_for_commit"
        ]

        collapse_predictions = [
            future
            for future in futures
            if future.get(
                "collapse_prediction",
                {},
            ).get(
                "collapse_state",
            )
            == "collapse_predicted"
        ]

        best_future = max(
            futures,
            key=lambda future: future.get(
                "commit_probability",
                0.0,
            ),
            default={},
        )

        report = {
            "system":
            "evolution_simulation_sandbox",

            "sandbox_mode":
            "parallel_future_evolution_rehearsal",

            "simulated_branch_count":
            len(
                branches,
            ),

            "parallel_futures":
            futures,

            "candidate_futures":
            candidate_futures,

            "collapse_predictions":
            collapse_predictions,

            "best_future":
            best_future,

            "sandbox_commit_gate":
            (
                "allow_candidate_commit"
                if candidate_futures
                else "simulation_only"
                if futures
                else "no_evolution_to_simulate"
            ),

            "epistemic_constraints":
            {
                "sandbox_survival_is_not_truth":
                True,

                "sandbox_rehearsal_cannot_commit_truth":
                True,

                "truth_commitments_are_read_only":
                True,
            },

            "sandbox_state":
            (
                "collapse_predicted"
                if collapse_predictions
                else "commit_candidate_available"
                if candidate_futures
                else "evolution_rehearsal_required"
                if futures
                else "idle"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.sandbox_history.append(
            report,
        )

        self.sandbox_history = (
            self.sandbox_history[-128:]
        )

        return report


evolution_sandbox = EvolutionSimulationSandbox()
