# ============================================
# NEXRYN COGNITIVE IDENTITY LAYER
# ============================================

from datetime import datetime


class CognitiveIdentityLayer:

    def __init__(self):

        self.identity_history = []

    def evaluate(
        self,
        context
    ):

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        long_horizon = governance.get(
            "long_horizon",
            {}
        )

        goal_drift = long_horizon.get(
            "long_term_goal_drift",
            0.0
        )

        homeostasis = governance.get(
            "homeostasis",
            {}
        )

        folding = context.get(
            "safe_concept_folding_report",
            {}
        )

        identity_risk = round(
            min(
                goal_drift * 0.45
                +
                folding.get(
                    "folding_pressure",
                    0.0
                )
                * 0.35
                +
                homeostasis.get(
                    "self_preservation_drive",
                    0.0
                )
                * 0.20,
                1.0
            ),
            4
        )

        report = {
            "layer":
            "cognitive_identity",

            "identity_state":
            (
                "identity_guarded"
                if identity_risk >= 0.60
                else "identity_watch"
                if identity_risk >= 0.35
                else "identity_stable"
            ),

            "identity_risk":
            identity_risk,

            "long_term_goal_drift":
            goal_drift,

            "homeostasis_state":
            homeostasis.get(
                "homeostasis_state",
                "unknown"
            ),

            "actions":
            (
                [
                    "preserve_causal_identity",
                    "block_overcompression",
                    "require_temporal_validation"
                ]
                if identity_risk >= 0.60
                else [
                    "monitor_goal_drift"
                ]
                if identity_risk >= 0.35
                else []
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.identity_history.append(
            report
        )

        self.identity_history = (
            self.identity_history[-32:]
        )

        return report


cognitive_identity_layer = (
    CognitiveIdentityLayer()
)
