# ============================================
# NEXRYN COGNITIVE PHARMACY ENGINE
# ============================================

from datetime import datetime

from core.cognitive_pharmacy.adaptive_pharmacology import (
    AdaptivePharmacology,
)
from core.cognitive_pharmacy.dependency_prevention import (
    PharmacyDependencyPrevention,
)
from core.cognitive_pharmacy.dosage_engine import (
    PharmacyDosageEngine,
    clamp,
)
from core.cognitive_pharmacy.medication_administration import (
    MedicationAdministration,
)
from core.cognitive_pharmacy.medication_registry import (
    MedicationRegistry,
)
from core.cognitive_pharmacy.pharmacological_ethics import (
    PharmacologicalEthics,
)
from core.cognitive_pharmacy.rebound_detection import (
    ReboundDetection,
)
from core.cognitive_pharmacy.recovery_analytics import (
    RecoveryAnalytics,
)
from core.cognitive_pharmacy.side_effect_monitor import (
    SideEffectMonitor,
)


class CognitivePharmacyEngine:

    def __init__(self):

        self.registry = MedicationRegistry()
        self.dosage_engine = PharmacyDosageEngine()
        self.dependency_prevention = PharmacyDependencyPrevention()
        self.rebound_detection = ReboundDetection()
        self.administration = MedicationAdministration()
        self.side_effect_monitor = SideEffectMonitor()
        self.ethics = PharmacologicalEthics()
        self.recovery_analytics = RecoveryAnalytics()
        self.adaptive_pharmacology = AdaptivePharmacology()
        self.administration_history = []

    def physiology_analytics(self, physician_report, dependency, side_effects):

        metrics = physician_report.get(
            "health_metrics",
            {},
        )

        return {
            "system": "semantic_physiology_analytics",
            "cognitive_fever": metrics.get("cognitive_fever_score", 0.0),
            "semantic_entropy": metrics.get("semantic_entropy", 0.0),
            "recursion_pressure": metrics.get("recursion_pressure", 0.0),
            "topology_stress": clamp(
                1.0 - metrics.get("topology_integrity", 1.0)
            ),
            "memory_congestion": metrics.get("memory_pressure", 0.0),
            "semantic_inflammation": metrics.get("semantic_instability", 0.0),
            "anchor_stability": metrics.get("semantic_anchor_integrity", 0.0),
            "lineage_integrity": metrics.get("continuity_ligament_stability", 0.0),
            "identity_coherence": clamp(
                1.0 - metrics.get("identity_drift", 0.0)
            ),
            "pharmacological_dependency": dependency.get("dependency_risk", 0.0),
            "semantic_toxicity": metrics.get("ontology_fragmentation", 0.0),
            "constitutional_health": metrics.get("constitutional_stability", 0.0),
            "side_effect_count": side_effects.get("side_effect_count", 0),
        }

    def dashboard(self, analytics, recovery):

        labels = [
            "cognitive_fever",
            "semantic_entropy",
            "semantic_inflammation",
            "recursion_pressure",
            "memory_congestion",
            "pharmacological_dependency",
            "semantic_toxicity",
            "constitutional_health",
            "topology_stress",
        ]

        visual = {}

        for label in labels:

            value = clamp(
                analytics.get(
                    label,
                    0.0,
                )
            )

            visual[label] = {
                "value": value,
                "bar": ("#" * int(value * 10)).ljust(10, "."),
            }

        visual["recovery_cycles"] = {
            "value": recovery.get(
                "recovery_progress",
                0.0,
            ),
            "bar": (
                "#"
                * int(
                    recovery.get(
                        "recovery_progress",
                        0.0,
                    )
                    * 10
                )
            ).ljust(10, "."),
        }

        return visual

    def homeostasis_model(self, dependency):

        return {
            "system": "cognitive_pharmacy_homeostasis_model",
            "goal": "ADAPTIVE_COGNITIVE_EQUILIBRIUM",
            "balances": [
                "exploration_vs_stability",
                "adaptation_vs_continuity",
                "neurogenesis_vs_preservation",
                "abstraction_vs_grounding",
                "evolution_vs_constitutional_integrity",
                "flexibility_vs_coherence",
                "creativity_vs_topology_safety",
            ],
            "maximizes_stability": False,
            "dependency_response": dependency.get(
                "response",
                "monitor",
            ),
        }

    def run_cycle(self, context):

        if not isinstance(context, dict):
            context = {}

        physician_report = context.get(
            "cognitive_physician_report",
            {},
        )

        governance_review = context.get(
            "governance_physician_review",
            context.get(
                "governance_kernel_report",
                {},
            ).get(
                "physician_review",
                {},
            ),
        )

        dependency = self.dependency_prevention.evaluate(
            context,
            physician_report,
        )

        dosage = self.dosage_engine.compute(
            physician_report,
            dependency,
        )

        rebound = self.rebound_detection.detect(
            context,
            dosage,
        )

        administration = self.administration.administer(
            self.registry,
            dosage,
            governance_review,
        )

        side_effects = self.side_effect_monitor.monitor(
            administration.get(
                "administrations",
                [],
            ),
            self.registry,
        )

        ethics = self.ethics.validate(
            administration.get(
                "administrations",
                [],
            ),
            governance_review,
        )

        recovery = self.recovery_analytics.analyze(
            physician_report,
            administration.get(
                "administrations",
                [],
            ),
        )

        adaptive = self.adaptive_pharmacology.adapt(
            dosage,
            rebound,
            dependency,
        )

        analytics = self.physiology_analytics(
            physician_report,
            dependency,
            side_effects,
        )

        report = {
            "system": "cognitive_pharmacy_engine",
            "role": "constitutional_cognitive_pharmacology_advisor",
            "non_emotional_system": True,
            "authority": "controlled_administration_after_governance",
            "governance_required": True,
            "medication_registry": self.registry.list_medications(),
            "dosage_plan": dosage,
            "dependency_prevention": dependency,
            "rebound_detection": rebound,
            "medication_administration": administration,
            "side_effect_monitor": side_effects,
            "pharmacological_ethics": ethics,
            "adaptive_pharmacology": adaptive,
            "recovery_analytics": recovery,
            "semantic_physiology_analytics": analytics,
            "homeostasis_model": self.homeostasis_model(
                dependency,
            ),
            "visual_dashboards": self.dashboard(
                analytics,
                recovery,
            ),
            "constitutional_workflow": [
                "physician",
                "diagnosis",
                "treatment_recommendation",
                "governance_kernel_approval",
                "constitutional_validation",
                "controlled_administration",
            ],
            "direct_mutation_prohibited": [
                "identity",
                "constitutional_invariants",
                "semantic_anchors",
                "lineage_history",
                "causal_history",
            ],
            "timestamp": str(datetime.utcnow()),
        }

        self.administration_history.append(report)
        self.administration_history = self.administration_history[-64:]

        return report


cognitive_pharmacy_engine = CognitivePharmacyEngine()
