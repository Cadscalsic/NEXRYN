# ============================================
# NEXRYN COGNITIVE PHARMACY REBOUND DETECTION
# ============================================

from core.cognitive_pharmacy.dosage_engine import (
    clamp,
)


class ReboundDetection:

    def detect(self, context, dosage):

        previous = context.get(
            "previous_pharmacy_report",
            {},
        ).get(
            "dosage_plan",
            {},
        )

        previous_sedation = previous.get(
            "SEMANTIC_SEDATIVE",
            0.0,
        )

        current_sedation = dosage.get(
            "SEMANTIC_SEDATIVE",
            0.0,
        )

        rebound_risk = clamp(
            max(
                0.0,
                previous_sedation - current_sedation,
            )
            * 0.65
            +
            context.get(
                "semantic_noise",
                0.0,
            )
            * 0.20
        )

        return {
            "system": "rebound_detection",
            "rebound_risk": rebound_risk,
            "rebound_detected": rebound_risk >= 0.52,
            "rebound_policy": (
                "gradual_taper_required"
                if rebound_risk >= 0.52
                else "standard_taper"
            ),
        }
