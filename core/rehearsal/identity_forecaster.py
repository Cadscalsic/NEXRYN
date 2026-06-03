# ============================================
# NEXRYN IDENTITY FORECASTER
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


class IdentityForecaster:

    def forecast(self, simulation_report, context):

        simulations = simulation_report.get(
            "simulations",
            [],
        )

        baseline_identity_risk = _clamp(
            context.get(
                "semantic_firewall_report",
                {},
            ).get(
                "identity_attack_detection",
                {},
            ).get(
                "attack_score",
                context.get(
                    "identity_attack_score",
                    0.0,
                ),
            ),
        )

        projected_drift = _clamp(
            sum(
                item.get(
                    "predicted_identity_delta",
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

        spine = context.get(
            "identity_stability_report",
            {},
        )

        continuity_verifier = spine.get(
            "continuity_verifier",
            {},
        )

        spine_continuity = _clamp(
            continuity_verifier.get(
                "continuity_score",
                0.50,
            ),
        )

        identity_continuity = _clamp(
            1.0
            -
            projected_drift * 0.62
            -
            baseline_identity_risk * 0.28
            +
            (
                spine_continuity
                -
                0.50
            )
            * 0.18
        )

        return {
            "system":
            "identity_forecaster",

            "baseline_identity_risk":
            baseline_identity_risk,

            "projected_identity_drift":
            projected_drift,

            "identity_continuity":
            identity_continuity,

            "identity_spine_continuity":
            spine_continuity,

            "forecast_state":
            (
                "continuity_preserved"
                if identity_continuity >= 0.62
                else "continuity_fragile"
                if identity_continuity >= 0.38
                else "continuity_at_risk"
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
