# ============================================
# NEXRYN BENEFICIAL MUTATION LEARNING
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


class BeneficialMutationLearning:

    def __init__(self):

        self.mutation_value_registry = {}

    def mutation_key(self, simulation):

        source = simulation.get(
            "source",
            {},
        )

        return (
            simulation.get(
                "candidate_type",
                "unknown",
            ),
            str(
                source.get(
                    "first",
                    source.get(
                        "concept",
                        "unknown",
                    ),
                ),
            ),
            str(
                source.get(
                    "second",
                    source.get(
                        "mutation_type",
                        "none",
                    ),
                ),
            ),
        )

    def learn(self, constructive_assessments):

        learned = []

        for assessment in constructive_assessments:

            simulation = assessment.get(
                "simulation",
                {},
            )

            key = self.mutation_key(
                simulation,
            )

            signal = _clamp(
                assessment.get(
                    "constructive_score",
                    0.0,
                ),
            )

            current = self.mutation_value_registry.get(
                key,
                0.20,
            )

            updated = _clamp(
                current * 0.72
                +
                signal * 0.28
            )

            self.mutation_value_registry[
                key
            ] = updated

            learned.append({
                "mutation_key":
                list(
                    key,
                ),

                "learned_value":
                updated,

                "constructive_score":
                signal,
            })

        average_learned_value = _clamp(
            sum(
                item.get(
                    "learned_value",
                    0.0,
                )
                for item in learned
            )
            /
            max(
                len(
                    learned,
                ),
                1,
            )
        )

        return {
            "system":
            "beneficial_mutation_learning",

            "learned_mutations":
            learned[:64],

            "registry_size":
            len(
                self.mutation_value_registry,
            ),

            "average_learned_value":
            average_learned_value,

            "learning_state":
            (
                "beneficial_patterns_learning"
                if learned
                else "awaiting_positive_examples"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
