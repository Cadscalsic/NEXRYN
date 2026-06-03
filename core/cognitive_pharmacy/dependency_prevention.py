# ============================================
# NEXRYN COGNITIVE PHARMACY DEPENDENCY PREVENTION
# ============================================

from core.cognitive_pharmacy.dosage_engine import (
    clamp,
)


class PharmacyDependencyPrevention:

    def evaluate(self, context, physician_report):

        physician_dependency = physician_report.get(
            "dependency_alerts",
            {},
        )

        risk = clamp(
            physician_dependency.get(
                "dependency_risk",
                0.0,
            )
            +
            context.get(
                "pharmacy_dependency_accumulation",
                0.0,
            )
            * 0.35
            +
            context.get(
                "sedation_reliance",
                0.0,
            )
            * 0.18
            +
            context.get(
                "rollback_usage_rate",
                0.0,
            )
            * 0.16
            +
            context.get(
                "exploration_suppression_rate",
                0.0,
            )
            * 0.16
        )

        detected = risk >= 0.58

        return {
            "system": "pharmacy_dependency_prevention",
            "dependency_detected": detected,
            "dependency_risk": risk,
            "detected_patterns": [
                pattern
                for pattern, active in [
                    ("sedation_addiction", risk >= 0.62),
                    ("rollback_dependence", context.get("rollback_usage_rate", 0.0) >= 0.58),
                    ("stabilization_dependence", context.get("stabilization_dependence", 0.0) >= 0.58),
                    ("exploration_suppression", context.get("exploration_suppression_rate", 0.0) >= 0.58),
                    ("semantic_rigidity", context.get("semantic_rigidity", 0.0) >= 0.58),
                ]
                if active
            ],
            "response": (
                "reduce_medication_effectiveness_and_restore_exploration"
                if detected
                else "monitor"
            ),
        }
