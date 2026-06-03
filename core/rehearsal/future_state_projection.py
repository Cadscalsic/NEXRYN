# ============================================
# NEXRYN FUTURE STATE PROJECTION
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


class FutureStateProjection:

    def project(self, simulation_report, identity_report, context):

        simulations = simulation_report.get(
            "simulations",
            [],
        )

        baseline_entropy = _clamp(
            context.get(
                "runtime_entropy",
                0.0,
            ),
        )

        entropy_delta = _clamp(
            sum(
                item.get(
                    "predicted_entropy_delta",
                    0.0,
                )
                for item in simulations
            )
            /
            max(
                len(
                    simulations,
                ),
                1,
            )
        )

        utility = _clamp(
            sum(
                item.get(
                    "predicted_utility",
                    0.0,
                )
                for item in simulations
            )
            /
            max(
                len(
                    simulations,
                ),
                1,
            )
        )

        identity_continuity = _clamp(
            identity_report.get(
                "identity_continuity",
                0.0,
            ),
        )

        future_stability = _clamp(
            identity_continuity * 0.42
            +
            (
                1.0 - entropy_delta
            )
            * 0.32
            +
            utility * 0.26
        )

        projected_entropy = _clamp(
            baseline_entropy
            +
            entropy_delta * 0.35
            -
            utility * 0.12
        )

        return {
            "system":
            "future_state_projection",

            "projected_entropy":
            projected_entropy,

            "average_entropy_delta":
            entropy_delta,

            "average_predicted_utility":
            utility,

            "future_stability":
            future_stability,

            "future_state":
            (
                "safe_evolution_window"
                if future_stability >= 0.62
                else "rehearsal_required"
                if future_stability >= 0.38
                else "unsafe_future"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
