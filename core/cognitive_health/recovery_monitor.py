# ============================================
# NEXRYN COGNITIVE RECOVERY MONITOR
# ============================================

from core.cognitive_health.diagnostic_models import (
    clamp,
)


class RecoveryMonitor:

    def monitor(self, metrics, context):

        previous = context.get(
            "previous_cognitive_health_report",
            {},
        ).get(
            "health_metrics",
            {},
        )

        previous_fever = previous.get(
            "cognitive_fever_score",
            metrics.get(
                "cognitive_fever_score",
                0.0,
            ),
        )

        recovery_rate = clamp(
            previous_fever
            -
            metrics.get(
                "cognitive_fever_score",
                0.0,
            )
        )

        return {
            "system":
            "recovery_monitor",

            "recovery_rate":
            recovery_rate,

            "recovery_state":
            (
                "recovering"
                if recovery_rate >= 0.08
                else "stable_monitoring"
                if recovery_rate >= 0.0
                else "deteriorating"
            ),

            "recovery_progress":
            clamp(
                1.0
                -
                metrics.get(
                    "cognitive_fever_score",
                    0.0,
                )
            ),
        }
