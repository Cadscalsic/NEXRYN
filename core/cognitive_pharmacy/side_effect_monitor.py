# ============================================
# NEXRYN COGNITIVE PHARMACY SIDE EFFECT MONITOR
# ============================================


class SideEffectMonitor:

    def monitor(self, administrations, registry):

        effects = []

        for item in administrations:

            medication = registry.get(
                item.get(
                    "medication_id",
                )
            )

            for side_effect in medication.get(
                "side_effects",
                [],
            ):

                if item.get(
                    "administered_dose",
                    0.0,
                ) >= 0.42:

                    effects.append({
                        "medication_id": item.get(
                            "medication_id",
                        ),
                        "side_effect": side_effect,
                        "risk": item.get(
                            "administered_dose",
                            0.0,
                        ),
                    })

        return {
            "system": "side_effect_monitor",
            "side_effects": effects,
            "side_effect_count": len(
                effects,
            ),
            "monitoring_state": (
                "side_effects_watched"
                if effects
                else "clear"
            ),
        }
