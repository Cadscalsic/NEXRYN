# ============================================
# NEXRYN COGNITIVE HEALTH TREATMENT PLANNER
# ============================================

from core.cognitive_health.cognitive_immunology import (
    CognitiveImmunology,
)
from core.cognitive_health.identity_healing import (
    IdentityHealing,
)
from core.cognitive_health.semantic_sedation import (
    SemanticSedation,
)
from core.cognitive_health.sleep_cycle_manager import (
    SleepCycleManager,
)
from core.cognitive_health.stabilization_protocols import (
    StabilizationProtocols,
)


class TreatmentPlanner:

    def __init__(self):

        self.semantic_sedation = SemanticSedation()
        self.identity_healing = IdentityHealing()
        self.cognitive_immunology = CognitiveImmunology()
        self.sleep_cycle_manager = SleepCycleManager()
        self.stabilization_protocols = StabilizationProtocols()

    def plan(self, diagnosis, metrics, dosage):

        treatments = [
            self.semantic_sedation.recommend(
                dosage,
            ),
            self.identity_healing.recommend(
                dosage,
            ),
            self.cognitive_immunology.coordinate(
                metrics,
                dosage,
            ),
        ]

        sleep = self.sleep_cycle_manager.plan(
            metrics,
        )

        stabilization = self.stabilization_protocols.build(
            diagnosis,
        )

        if diagnosis.get(
            "state",
        ) in [
            "COGNITIVE_TRAUMA",
            "SEMANTIC_COLLAPSE_RISK",
        ]:

            treatments.append({
                "treatment":
                "TRAUMA_RECOVERY",

                "intensity":
                dosage.get(
                    "trauma_recovery",
                    0.0,
                ),

                "handles":
                [
                    "rollback_recovery",
                    "post_collapse_healing",
                    "fragmentation_repair",
                    "causal_restoration",
                ],
            })

        treatments.append({
            "treatment":
            "ONTOLOGICAL_DETOXIFICATION",

            "intensity":
            dosage.get(
                "ontological_detox",
                0.0,
            ),

            "removes":
            [
                "dead_semantic_bridges",
                "unstable_hybrids",
                "high_entropy_concepts",
                "toxic_recursive_loops",
            ],
        })

        return {
            "system":
            "treatment_planner",

            "recommendations":
            treatments,

            "sleep_cycle":
            sleep,

            "stabilization_protocols":
            stabilization,

            "authority":
            "recommendation_only",
        }
