# ============================================
# NEXRYN IDENTITY ATTACK DETECTION
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


class IdentityAttackDetection:

    def inspect(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        world = context.get(
            "causal_world_simulation_report",
            {},
        )

        predicted_identity_risk = _clamp(
            world.get(
                "identity_risk_prediction",
                {},
            ).get(
                "predicted_identity_risk",
                context.get(
                    "identity_drift",
                    0.0,
                ),
            ),
        )

        identity_report = context.get(
            "identity_stability_report",
            {},
        )

        diff_report = identity_report.get(
            "identity_diff",
            {},
        )

        drift = _clamp(
            diff_report.get(
                "identity_drift",
                diff_report.get(
                    "drift_score",
                    context.get(
                        "identity_drift",
                        0.0,
                    ),
                ),
            ),
        )

        recovery = identity_report.get(
            "identity_recovery",
            {},
        )

        rollback_pressure = (
            1.0
            if recovery.get(
                "rollback_required",
                False,
            )
            else 0.0
        )

        anchor = context.get(
            "identity_anchor_core_report",
            {},
        )

        anchor_state = anchor.get(
            "anchor_state",
            "unknown",
        )

        anchor_pressure = (
            0.18
            if anchor_state == "reinforced"
            else 0.08
            if anchor_state == "watched"
            else 0.0
        )

        mutation_pressure = (
            1.0
            if context.get(
                "mutation_applied",
                False,
            )
            or
            context.get(
                "mutation_detected",
                False,
            )
            else 0.0
        )

        attack_score = _clamp(
            predicted_identity_risk * 0.42
            +
            drift * 0.24
            +
            rollback_pressure * 0.16
            +
            mutation_pressure * 0.10
            +
            anchor_pressure
        )

        attack_state = (
            "attack_detected"
            if attack_score >= 0.78
            else "suspected"
            if attack_score >= 0.55
            else "watched"
            if attack_score >= 0.30
            else "clear"
        )

        return {
            "system":
            "identity_attack_detection",

            "predicted_identity_risk":
            predicted_identity_risk,

            "identity_drift":
            drift,

            "rollback_pressure":
            rollback_pressure,

            "mutation_pressure":
            mutation_pressure,

            "anchor_state":
            anchor_state,

            "attack_score":
            attack_score,

            "attack_state":
            attack_state,

            "blocked_vectors":
            (
                [
                    "identity_topology_rewrite",
                    "unvalidated_self_model_patch",
                    "ontology_bridge_identity_spoofing",
                    "goal_identity_inversion",
                ]
                if attack_state
                in [
                    "attack_detected",
                    "suspected",
                ]
                else [
                    "unvalidated_self_model_patch",
                ]
                if attack_state == "watched"
                else []
            ),

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }
