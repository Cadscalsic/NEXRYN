# ============================================
# NEXRYN CAUSAL GAIN ESTIMATOR
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


class CausalGainEstimator:

    def estimate(self, simulation, pattern_value_report):

        source = simulation.get(
            "source",
            {},
        )

        before = _clamp(
            source.get(
                "baseline_utility",
                source.get(
                    "prior_utility",
                    0.32,
                ),
            ),
        )

        after = _clamp(
            simulation.get(
                "predicted_utility",
                pattern_value_report.get(
                    "pattern_value",
                    0.0,
                ),
            ),
        )

        entropy_delta = _clamp(
            simulation.get(
                "predicted_entropy_delta",
                1.0,
            ),
        )

        identity_delta = _clamp(
            simulation.get(
                "predicted_identity_delta",
                1.0,
            ),
        )

        raw_gain = _clamp(
            after
            -
            before,
            minimum=0.0,
        )

        bounded_gain = _clamp(
            raw_gain * 0.52
            +
            pattern_value_report.get(
                "causal_alignment",
                0.0,
            )
            * 0.24
            +
            (
                1.0 - entropy_delta
            )
            * 0.14
            +
            (
                1.0 - identity_delta
            )
            * 0.10
        )

        return {
            "causal_gain":
            bounded_gain,

            "raw_utility_gain":
            raw_gain,

            "utility_before":
            before,

            "utility_after":
            after,

            "entropy_delta":
            entropy_delta,

            "identity_delta":
            identity_delta,

            "gain_state":
            (
                "breakthrough_candidate"
                if bounded_gain >= 0.58
                else "useful_gain"
                if bounded_gain >= 0.34
                else "weak_gain"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
