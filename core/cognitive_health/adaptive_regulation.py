# ============================================
# NEXRYN ADAPTIVE REGULATION
# ============================================


class AdaptiveRegulation:

    def regulate(self, diagnosis, dosage, dependency):

        if dependency.get(
            "dependency_detected",
            False,
        ):

            posture = "restore_cognitive_flexibility"

        elif diagnosis.get(
            "severity",
            0.0,
        ) >= 0.72:

            posture = "controlled_stabilization"

        else:

            posture = "adaptive_monitoring"

        return {
            "system":
            "adaptive_regulation",

            "regulation_posture":
            posture,

            "treatment_adjustment":
            (
                "reduce_strength_and_encourage_safe_exploration"
                if dependency.get(
                    "dependency_detected",
                    False,
                )
                else "dynamic_dosage"
            ),

            "direct_runtime_control":
            False,
        }
