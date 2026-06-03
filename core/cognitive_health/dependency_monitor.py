# ============================================
# NEXRYN PHYSICIAN DEPENDENCY MONITOR
# ============================================

from core.cognitive_health.diagnostic_models import (
    clamp,
)


class DependencyMonitor:

    def evaluate(self, context):

        sedation_reliance = clamp(
            context.get(
                "sedation_reliance",
                0.0,
            )
        )

        rollback_usage = clamp(
            context.get(
                "rollback_usage_rate",
                0.0,
            )
        )

        exploration_suppression = clamp(
            context.get(
                "exploration_suppression_rate",
                0.0,
            )
        )

        stabilization_dependence = clamp(
            context.get(
                "stabilization_dependence",
                0.0,
            )
        )

        dependency_risk = clamp(
            sedation_reliance * 0.30
            +
            rollback_usage * 0.25
            +
            exploration_suppression * 0.25
            +
            stabilization_dependence * 0.20
        )

        detected = dependency_risk >= 0.58

        return {
            "system":
            "dependency_monitor",

            "dependency_detected":
            detected,

            "dependency_risk":
            dependency_risk,

            "alerts":
            [
                alert
                for alert, active in [
                    ("excessive_sedation_reliance", sedation_reliance >= 0.62),
                    ("pathological_rollback_usage", rollback_usage >= 0.58),
                    ("avoidance_of_exploration", exploration_suppression >= 0.58),
                    ("chronic_stabilization_dependence", stabilization_dependence >= 0.62),
                ]
                if active
            ],

            "dependency_response":
            (
                "reduce_treatment_strength_and_restore_flexibility"
                if detected
                else "monitor"
            ),
        }
