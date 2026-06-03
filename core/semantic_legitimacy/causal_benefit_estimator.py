# ============================================
# NEXRYN CAUSAL BENEFIT ESTIMATOR
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


class CausalBenefitEstimator:

    def estimate(self, context):

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        future = rehearsal.get(
            "future_state_projection",
            {},
        )

        identity = rehearsal.get(
            "identity_forecaster",
            {},
        )

        future_stability = _clamp(
            future.get(
                "future_stability",
                0.0,
            ),
        )

        predicted_utility = _clamp(
            future.get(
                "average_predicted_utility",
                0.0,
            ),
        )

        identity_continuity = _clamp(
            identity.get(
                "identity_continuity",
                0.0,
            ),
        )

        entropy_delta = _clamp(
            future.get(
                "average_entropy_delta",
                1.0,
            ),
        )

        benefit_score = _clamp(
            future_stability * 0.34
            +
            predicted_utility * 0.30
            +
            identity_continuity * 0.22
            +
            (
                1.0 - entropy_delta
            )
            * 0.14
        )

        return {
            "system":
            "causal_benefit_estimator",

            "causal_benefit_score":
            benefit_score,

            "future_stability":
            future_stability,

            "predicted_utility":
            predicted_utility,

            "identity_continuity":
            identity_continuity,

            "entropy_delta":
            entropy_delta,

            "benefit_state":
            (
                "beneficial"
                if benefit_score >= 0.58
                else "plausible"
                if benefit_score >= 0.35
                else "unproven"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
