# ============================================
# NEXRYN NOVEL PATTERN VALUE
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


class NovelPatternValue:

    def evaluate(self, simulation):

        source = simulation.get(
            "source",
            {},
        )

        novelty = _clamp(
            simulation.get(
                "novelty",
                source.get(
                    "novelty",
                    source.get(
                        "novelty_score",
                        0.0,
                    ),
                ),
            ),
        )

        causal_alignment = _clamp(
            simulation.get(
                "causal_alignment",
                source.get(
                    "causal_alignment",
                    0.0,
                ),
            ),
        )

        utility = _clamp(
            simulation.get(
                "predicted_utility",
                0.0,
            ),
        )

        entropy_delta = _clamp(
            simulation.get(
                "predicted_entropy_delta",
                1.0,
            ),
        )

        pattern_value = _clamp(
            novelty * 0.32
            +
            causal_alignment * 0.30
            +
            utility * 0.26
            +
            (
                1.0 - entropy_delta
            )
            * 0.12
        )

        return {
            "pattern_value":
            pattern_value,

            "novelty":
            novelty,

            "causal_alignment":
            causal_alignment,

            "predicted_utility":
            utility,

            "entropy_delta":
            entropy_delta,

            "pattern_value_state":
            (
                "high_value"
                if pattern_value >= 0.62
                else "promising"
                if pattern_value >= 0.40
                else "low_value"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
