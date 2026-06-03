# ============================================
# NEXRYN PERSISTENT IDENTITY CORE
# ============================================

from datetime import datetime


class IdentityCore:

    def __init__(self):

        self.identity_history = []

    def compute_identity_drift(self, context):

        identity = context.get(
            "cognitive_identity_report",
            {}
        )

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        long_horizon = governance.get(
            "long_horizon",
            {}
        )

        return round(
            min(
                identity.get(
                    "identity_risk",
                    0.0
                )
                * 0.55
                +
                long_horizon.get(
                    "long_term_goal_drift",
                    0.0
                )
                * 0.45,
                1.0
            ),
            4
        )

    def preserve_core_goals(self, drift):

        if drift >= 0.55:

            return [
                "preserve_execution_grounding",
                "preserve_ontology_identity",
                "preserve_reward_alignment"
            ]

        return [
            "monitor_core_goals"
        ]

    def detect_behavior_shift(self, context):

        arbitration = context.get(
            "executive_arbitration_report",
            {}
        )

        action_count = len(
            arbitration.get(
                "selected_actions",
                []
            )
        )

        return {
            "shift_detected":
            action_count >= 14,

            "action_count":
            action_count
        }

    def regulate_strategy_alignment(self, drift):

        return (
            "strict_alignment"
            if drift >= 0.55
            else "watch_alignment"
            if drift >= 0.30
            else "normal_alignment"
        )

    def protect_cognitive_continuity(self, context):

        drift = self.compute_identity_drift(
            context
        )

        behavior_shift = self.detect_behavior_shift(
            context
        )

        report = {
            "core":
            "persistent_identity",

            "identity_drift":
            drift,

            "continuity_state":
            (
                "protected"
                if drift >= 0.55
                else "watched"
                if drift >= 0.30
                else "stable"
            ),

            "core_goal_policy":
            self.preserve_core_goals(
                drift
            ),

            "behavior_shift":
            behavior_shift,

            "strategy_alignment":
            self.regulate_strategy_alignment(
                drift
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
            self.identity_history[-64:]
        )

        return report


identity_core = (
    IdentityCore()
)
