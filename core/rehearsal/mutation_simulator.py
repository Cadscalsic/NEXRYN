# ============================================
# NEXRYN MUTATION SIMULATOR
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


class MutationSimulator:

    def collect_candidates(self, context):

        firewall = context.get(
            "semantic_firewall_report",
            {},
        )

        sandbox = firewall.get(
            "concept_sandboxing",
            {},
        )

        candidates = []

        for event in sandbox.get(
            "sandboxed_events",
            [],
        ):

            candidates.append({
                "candidate_type":
                event.get(
                    "event_type",
                    "unknown",
                ),

                "source":
                event.get(
                    "source",
                    {},
                ),

                "sandbox_pressure":
                event.get(
                    "sandbox_pressure",
                    0.0,
                ),
            })

        mutation_candidates = context.get(
            "mutation_candidates",
            [],
        )

        if isinstance(
            mutation_candidates,
            dict,
        ):

            mutation_candidates = mutation_candidates.get(
                "value",
                mutation_candidates,
            )

        if isinstance(
            mutation_candidates,
            dict,
        ):

            mutation_candidates = [
                mutation_candidates,
            ]

        if not isinstance(
            mutation_candidates,
            list,
        ):

            mutation_candidates = []

        for item in mutation_candidates:

            if not isinstance(
                item,
                dict,
            ):

                continue

            candidates.append({
                "candidate_type":
                "mutation",

                "source":
                item,

                "sandbox_pressure":
                item.get(
                    "risk",
                    0.0,
                ),
            })

        return candidates[:96]

    def simulate_candidate(self, candidate, index, context):

        source = candidate.get(
            "source",
            {},
        )

        source_risk = _clamp(
            source.get(
                "merge_risk",
                source.get(
                    "risk",
                    candidate.get(
                        "sandbox_pressure",
                        0.0,
                    ),
                ),
            ),
        )

        novelty = _clamp(
            source.get(
                "novelty",
                source.get(
                    "novelty_score",
                    0.50,
                ),
            ),
        )

        causal_alignment = _clamp(
            source.get(
                "causal_overlap",
                source.get(
                    "causal_alignment",
                    1.0 - source_risk,
                ),
            ),
        )

        predicted_entropy_delta = _clamp(
            source_risk * 0.45
            +
            novelty * 0.20
            -
            causal_alignment * 0.18
            +
            context.get(
                "runtime_entropy",
                0.0,
            )
            * 0.12
        )

        predicted_identity_delta = _clamp(
            source_risk * 0.36
            +
            (
                1.0 - causal_alignment
            )
            * 0.32
            -
            novelty * 0.08
        )

        predicted_utility = _clamp(
            novelty * 0.38
            +
            causal_alignment * 0.32
            +
            (
                1.0 - source_risk
            )
            * 0.20
            +
            (
                1.0 - predicted_entropy_delta
            )
            * 0.10
        )

        return {
            "simulation_id":
            f"mutation_rehearsal:{index + 1}",

            "candidate_type":
            candidate.get(
                "candidate_type",
                "unknown",
            ),

            "source":
            source,

            "predicted_entropy_delta":
            predicted_entropy_delta,

            "predicted_identity_delta":
            predicted_identity_delta,

            "predicted_utility":
            predicted_utility,

            "causal_alignment":
            causal_alignment,

            "novelty":
            novelty,

            "simulation_state":
            (
                "constructive"
                if predicted_utility >= 0.52
                and predicted_identity_delta <= 0.42
                else "ambiguous"
                if predicted_utility >= 0.30
                else "harmful"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        candidates = self.collect_candidates(
            context,
        )

        simulations = [
            self.simulate_candidate(
                candidate,
                index,
                context,
            )
            for index, candidate in enumerate(
                candidates,
            )
        ]

        constructive_count = len([
            item
            for item in simulations
            if item.get(
                "simulation_state",
            )
            == "constructive"
        ])

        return {
            "system":
            "mutation_simulator",

            "candidate_count":
            len(
                candidates,
            ),

            "simulations":
            simulations,

            "constructive_count":
            constructive_count,

            "simulation_state":
            (
                "constructive_paths_found"
                if constructive_count
                else "no_safe_path_yet"
                if simulations
                else "idle"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
