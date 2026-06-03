# ============================================
# NEXRYN IDENTITY FIREWALL
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


class IdentityFirewall:

    def inspect(self, context):

        world = context.get(
            "causal_world_simulation_report",
            {},
        )

        predicted_identity = world.get(
            "identity_risk_prediction",
            {},
        ).get(
            "predicted_identity_risk",
            context.get(
                "identity_drift",
                0.0,
            ),
        )

        anchor = context.get(
            "identity_anchor_core_report",
            {},
        )

        anchor_state = anchor.get(
            "anchor_state",
            "unknown",
        )

        firewall_pressure = _clamp(
            predicted_identity * 0.75
            +
            (
                0.20
                if anchor_state == "reinforced"
                else 0.08
                if anchor_state == "watched"
                else 0.0
            )
        )

        return {
            "system":
            "identity_firewall",

            "predicted_identity_risk":
            _clamp(
                predicted_identity,
            ),

            "firewall_pressure":
            firewall_pressure,

            "firewall_state":
            (
                "sealed"
                if firewall_pressure >= 0.72
                else "filtered"
                if firewall_pressure >= 0.42
                else "open"
            ),

            "blocked_payloads":
            (
                [
                    "identity_mutating_macro",
                    "unsafe_goal_rewrite",
                    "unvalidated_self_model_patch",
                ]
                if firewall_pressure >= 0.72
                else [
                    "unvalidated_self_model_patch",
                ]
                if firewall_pressure >= 0.42
                else []
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
