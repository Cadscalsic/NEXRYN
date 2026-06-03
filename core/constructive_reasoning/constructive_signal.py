# ============================================
# NEXRYN CONSTRUCTIVE SIGNAL
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


class ConstructiveSignal:

    def combine(self, simulation, pattern_value_report, gain_report):

        identity_delta = _clamp(
            simulation.get(
                "predicted_identity_delta",
                1.0,
            ),
        )

        entropy_delta = _clamp(
            simulation.get(
                "predicted_entropy_delta",
                1.0,
            ),
        )

        constructive_score = _clamp(
            pattern_value_report.get(
                "pattern_value",
                0.0,
            )
            * 0.36
            +
            gain_report.get(
                "causal_gain",
                0.0,
            )
            * 0.34
            +
            (
                1.0 - identity_delta
            )
            * 0.18
            +
            (
                1.0 - entropy_delta
            )
            * 0.12
        )

        return {
            "constructive_score":
            constructive_score,

            "constructive_state":
            (
                "constructive"
                if constructive_score >= 0.54
                else "promising"
                if constructive_score >= 0.34
                else "not_constructive"
            ),

            "reasoning":
            {
                "pattern_value":
                pattern_value_report.get(
                    "pattern_value",
                    0.0,
                ),

                "causal_gain":
                gain_report.get(
                    "causal_gain",
                    0.0,
                ),

                "identity_preservation":
                _clamp(
                    1.0 - identity_delta,
                ),

                "entropy_bound":
                _clamp(
                    1.0 - entropy_delta,
                ),
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
