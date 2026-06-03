# ============================================
# NEXRYN CONSTRUCTIVE MUTATION DETECTION
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


class ConstructiveMutationDetection:

    def detect(self, context):

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        simulations = rehearsal.get(
            "mutation_simulator",
            {},
        ).get(
            "simulations",
            [],
        )

        constructive = [
            item
            for item in simulations
            if item.get(
                "simulation_state",
            )
            == "constructive"
        ]

        discovery = context.get(
            "constructive_reasoning_report",
            {},
        )

        discovered_constructive = [
            item.get(
                "simulation",
                item,
            )
            for item in discovery.get(
                "constructive_assessments",
                [],
            )
        ]

        constructive.extend(
            discovered_constructive,
        )

        constructive_signal = _clamp(
            max(
                (
                    len(
                        constructive,
                    )
                    /
                    max(
                        len(
                            simulations,
                        ),
                        1,
                    )
                ),
                discovery.get(
                    "constructive_signal",
                    0.0,
                ),
            )
        )

        average_utility = _clamp(
            sum(
                item.get(
                    "predicted_utility",
                    0.0,
                )
                for item in constructive
            )
            /
            max(
                len(
                    constructive,
                ),
                1,
            )
        )

        average_utility = _clamp(
            max(
                average_utility,
                discovery.get(
                    "beneficial_mutation_learning",
                    {},
                ).get(
                    "average_learned_value",
                    0.0,
                ),
            )
        )

        return {
            "system":
            "constructive_mutation_detection",

            "constructive_signal":
            constructive_signal,

            "average_constructive_utility":
            average_utility,

            "constructive_mutations":
            constructive[:32],

            "constructive_reasoning":
            discovery,

            "mutation_legitimacy_state":
            (
                "constructive"
                if constructive_signal >= 0.50
                and average_utility >= 0.48
                else "mixed"
                if constructive_signal > 0.0
                else "not_established"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
