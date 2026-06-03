# ============================================
# NEXRYN CONTINUITY VERIFIER
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


class ContinuityVerifier:

    def verify(self, anchor_report, graph_report, context):

        rehearsal = context.get(
            "causal_rehearsal_report",
            {},
        )

        forecast = rehearsal.get(
            "identity_forecaster",
            {},
        )

        forecast_continuity = _clamp(
            forecast.get(
                "identity_continuity",
                anchor_report.get(
                    "identity_continuity",
                    0.0,
                ),
            ),
        )

        graph_consistency = _clamp(
            graph_report.get(
                "consistency_score",
                0.0,
            ),
        )

        anchor_strength = _clamp(
            anchor_report.get(
                "anchor_strength",
                0.0,
            ),
        )

        continuity_score = _clamp(
            forecast_continuity * 0.40
            +
            graph_consistency * 0.34
            +
            anchor_strength * 0.26
        )

        violations = []

        if forecast_continuity < 0.62:

            violations.append(
                "fragile_identity_forecast",
            )

        if graph_consistency < 0.48:

            violations.append(
                "self_consistency_fragmentation",
            )

        if anchor_strength < 0.50:

            violations.append(
                "weak_identity_anchor",
            )

        return {
            "system":
            "continuity_verifier",

            "continuity_score":
            continuity_score,

            "forecast_identity_continuity":
            forecast_continuity,

            "graph_consistency":
            graph_consistency,

            "anchor_strength":
            anchor_strength,

            "violations":
            violations,

            "verification_state":
            (
                "verified"
                if continuity_score >= 0.72
                and not violations
                else "fragile_verified"
                if continuity_score >= 0.52
                else "blocked_for_identity_repair"
            ),

            "required_checks":
            [
                "core_principle_preservation",
                "causal_history_explanation",
                "architectural_invariant_preservation",
                "protected_cognition_law_compliance",
            ],

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
