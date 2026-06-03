# ============================================
# NEXRYN ADAPTIVE DOSAGE CONTROLLER
# ============================================

from core.cognitive_health.diagnostic_models import (
    clamp,
)


class DosageController:

    def compute(self, metrics, diagnosis, dependency):

        fever = metrics.get(
            "cognitive_fever_score",
            0.0,
        )

        drift = metrics.get(
            "identity_drift",
            0.0,
        )

        pressure = metrics.get(
            "semantic_instability",
            0.0,
        )

        constitutional_risk = 1.0 - metrics.get(
            "constitutional_stability",
            1.0,
        )

        dependency_risk = dependency.get(
            "dependency_risk",
            0.0,
        )

        dampener = 1.0 - dependency_risk * 0.35

        return {
            "system":
            "dosage_controller",

            "dosage_is_static":
            False,

            "semantic_sedation":
            clamp(
                (fever * 0.45 + pressure * 0.35)
                * dampener
            ),

            "identity_stabilization":
            clamp(
                (drift * 0.55 + constitutional_risk * 0.25)
                * dampener
            ),

            "cognitive_immunology":
            clamp(
                (
                    metrics.get(
                        "latent_conflict_density",
                        0.0,
                    )
                    * 0.50
                    +
                    pressure * 0.30
                )
                * dampener
            ),

            "sleep_cycle":
            clamp(
                (
                    metrics.get(
                        "cognitive_fatigue",
                        0.0,
                    )
                    * 0.45
                    +
                    fever * 0.35
                )
                * dampener
            ),

            "trauma_recovery":
            clamp(
                (
                    1.0
                    if diagnosis.get(
                        "state",
                    )
                    == "COGNITIVE_TRAUMA"
                    else drift * 0.35
                    +
                    constitutional_risk * 0.25
                )
                * dampener
            ),

            "ontological_detox":
            clamp(
                (
                    metrics.get(
                        "ontology_fragmentation",
                        0.0,
                    )
                    * 0.45
                    +
                    metrics.get(
                        "fusion_failure_rate",
                        0.0,
                    )
                    * 0.25
                )
                * dampener
            ),
        }
