# ============================================
# NEXRYN COGNITIVE PHARMACY RECOVERY ANALYTICS
# ============================================

from core.cognitive_pharmacy.dosage_engine import (
    clamp,
)


class RecoveryAnalytics:

    def analyze(self, physician_report, administrations):

        metrics = physician_report.get(
            "health_metrics",
            {},
        )

        recovery_progress = clamp(
            1.0
            -
            metrics.get(
                "cognitive_fever_score",
                0.0,
            )
        )

        active_medications = len([
            item
            for item in administrations
            if item.get(
                "administered_dose",
                0.0,
            )
            > 0
        ])

        return {
            "system": "recovery_analytics",
            "recovery_progress": recovery_progress,
            "active_medication_count": active_medications,
            "recovery_state": (
                "recovering_under_controlled_administration"
                if active_medications
                else "awaiting_governance_or_no_medication_needed"
            ),
        }
