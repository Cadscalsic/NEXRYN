# ============================================
# NEXRYN COGNITIVE PHYSICIAN ENGINE
# ============================================

from datetime import datetime

from core.cognitive_health.adaptive_regulation import (
    AdaptiveRegulation,
)
from core.cognitive_health.constitutional_medical_ethics import (
    ConstitutionalMedicalEthics,
)
from core.cognitive_health.dependency_monitor import (
    DependencyMonitor,
)
from core.cognitive_health.diagnostic_models import (
    DIAGNOSTIC_STATES,
    clamp,
    collect_health_metrics,
)
from core.cognitive_health.dosage_controller import (
    DosageController,
)
from core.cognitive_health.homeostasis_controller import (
    HomeostasisController,
)
from core.cognitive_health.recovery_monitor import (
    RecoveryMonitor,
)
from core.cognitive_health.symptom_analysis import (
    SymptomAnalyzer,
)
from core.cognitive_health.treatment_planner import (
    TreatmentPlanner,
)


class CognitivePhysicianEngine:

    def __init__(self):

        self.symptom_analyzer = SymptomAnalyzer()
        self.dependency_monitor = DependencyMonitor()
        self.dosage_controller = DosageController()
        self.treatment_planner = TreatmentPlanner()
        self.recovery_monitor = RecoveryMonitor()
        self.homeostasis_controller = HomeostasisController()
        self.medical_ethics = ConstitutionalMedicalEthics()
        self.adaptive_regulation = AdaptiveRegulation()
        self.treatment_history = []

    def diagnose(self, metrics, symptoms):

        fever = metrics.get(
            "cognitive_fever_score",
            0.0,
        )
        entropy = metrics.get(
            "semantic_entropy",
            0.0,
        )
        drift = metrics.get(
            "identity_drift",
            0.0,
        )
        recursion = metrics.get(
            "recursion_pressure",
            0.0,
        )
        fragmentation = metrics.get(
            "ontology_fragmentation",
            0.0,
        )
        memory = metrics.get(
            "memory_pressure",
            0.0,
        )
        constitutional = metrics.get(
            "constitutional_stability",
            1.0,
        )

        state = "HEALTHY_EXPLORATION"

        if fever >= 0.82 or entropy >= 0.86:
            state = "SEMANTIC_COLLAPSE_RISK"
        elif constitutional <= 0.34:
            state = "CONSTITUTIONAL_INSTABILITY"
        elif drift >= 0.68:
            state = "IDENTITY_FRACTURE_RISK"
        elif recursion >= 0.78:
            state = "RECURSIVE_EXHAUSTION"
        elif fragmentation >= 0.72:
            state = "ONTOLOGICAL_FEVER"
        elif memory >= 0.76:
            state = "MEMORY_CONGESTION"
        elif fever >= 0.64:
            state = "SEMANTIC_INFLAMMATION"
        elif metrics.get(
            "merge_exhaustion",
            0.0,
        ) >= 0.68:
            state = "MERGE_ADDICTION"
        elif metrics.get(
            "exploration_overload",
            0.0,
        ) >= 0.70:
            state = "TEMPORARY_OVERLOAD"
        elif drift >= 0.34:
            state = "PRODUCTIVE_DRIFT"

        severity = clamp(
            fever * 0.34
            +
            entropy * 0.18
            +
            drift * 0.16
            +
            recursion * 0.12
            +
            fragmentation * 0.10
            +
            memory * 0.10
        )

        confidence = clamp(
            0.50
            +
            symptoms.get(
                "symptom_load",
                0.0,
            )
            * 0.35
            +
            len(
                symptoms.get(
                    "symptoms",
                    [],
                )
            )
            / 24
        )

        affected = [
            item.get(
                "metric",
            )
            for item in symptoms.get(
                "symptoms",
                [],
            )
        ]

        return {
            "system":
            "diagnostic_models",

            "state":
            state,

            "known_states":
            DIAGNOSTIC_STATES,

            "severity":
            severity,

            "confidence":
            confidence,

            "affected_systems":
            affected,

            "risk_escalation":
            (
                "critical"
                if severity >= 0.76
                else "elevated"
                if severity >= 0.52
                else "low"
            ),

            "constitutional_implications":
            (
                "recommend_governance_review_before_runtime_change"
                if severity >= 0.52
                else "standard_governance_review"
            ),
        }

    def visualizations(self, metrics, recovery):

        keys = {
            "cognitive_fever":
            "cognitive_fever_score",
            "semantic_entropy":
            "semantic_entropy",
            "identity_stability":
            "continuity_ligament_stability",
            "lineage_health":
            "semantic_anchor_integrity",
            "conflict_density":
            "latent_conflict_density",
            "recovery_progress":
            None,
            "immune_activity":
            "semantic_instability",
            "constitutional_integrity":
            "constitutional_stability",
            "topology_stress":
            "topology_integrity",
        }

        visual = {}

        for label, key in keys.items():

            value = (
                recovery.get(
                    "recovery_progress",
                    0.0,
                )
                if key is None
                else metrics.get(
                    key,
                    0.0,
                )
            )

            filled = int(
                clamp(
                    value,
                )
                * 10
            )

            visual[
                label
            ] = {
                "value":
                clamp(
                    value,
                ),

                "bar":
                ("#" * filled).ljust(
                    10,
                    ".",
                ),
            }

        return visual

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        metrics = collect_health_metrics(
            context,
        )

        symptoms = self.symptom_analyzer.analyze(
            metrics,
        )

        diagnosis = self.diagnose(
            metrics,
            symptoms,
        )

        dependency = self.dependency_monitor.evaluate(
            context,
        )

        dosage = self.dosage_controller.compute(
            metrics,
            diagnosis,
            dependency,
        )

        treatment = self.treatment_planner.plan(
            diagnosis,
            metrics,
            dosage,
        )

        ethics = self.medical_ethics.assess(
            treatment.get(
                "recommendations",
                [],
            )
        )

        recovery = self.recovery_monitor.monitor(
            metrics,
            context,
        )

        homeostasis = self.homeostasis_controller.balance(
            metrics,
            dependency,
        )

        adaptive = self.adaptive_regulation.regulate(
            diagnosis,
            dosage,
            dependency,
        )

        recommendations = {
            "submit_to":
            "governance_kernel",

            "direct_runtime_control":
            False,

            "recommended_treatments":
            treatment.get(
                "recommendations",
                [],
            ),

            "recommended_protocols":
            treatment.get(
                "stabilization_protocols",
                {},
            ).get(
                "protocols",
                [],
            ),

            "sleep_cycle":
            treatment.get(
                "sleep_cycle",
                {},
            ),
        }

        report = {
            "system":
            "cognitive_physician_engine",

            "role":
            "constitutional_cognitive_physician_advisor",

            "non_emotional_system":
            True,

            "authority":
            "advisory_only",

            "health_metrics":
            metrics,

            "symptom_analysis":
            symptoms,

            "diagnosis_report":
            diagnosis,

            "semantic_health_map":
            metrics,

            "fever_analytics":
            {
                "cognitive_fever_score":
                metrics.get(
                    "cognitive_fever_score",
                    0.0,
                ),

                "fever_state":
                diagnosis.get(
                    "state",
                ),
            },

            "drift_analysis":
            {
                "identity_drift":
                metrics.get(
                    "identity_drift",
                    0.0,
                ),

                "semantic_instability":
                metrics.get(
                    "semantic_instability",
                    0.0,
                ),
            },

            "dosage_controller":
            dosage,

            "recovery_plan":
            treatment,

            "treatment_history":
            self.treatment_history[-32:],

            "dependency_alerts":
            dependency,

            "constitutional_safety_assessment":
            ethics,

            "semantic_immune_report":
            treatment.get(
                "recommendations",
                [],
            )[2],

            "stabilization_recommendations":
            recommendations,

            "homeostasis_controller":
            homeostasis,

            "adaptive_regulation":
            adaptive,

            "runtime_visualizations":
            self.visualizations(
                metrics,
                recovery,
            ),

            "governance_submission":
            {
                "submitted":
                True,

                "target":
                "governance_kernel",

                "physician_can_bypass_governance":
                False,
            },

            "timestamp":
            str(
                datetime.utcnow()
            ),
        }

        self.treatment_history.append({
            "diagnosis":
            diagnosis.get(
                "state",
            ),

            "severity":
            diagnosis.get(
                "severity",
                0.0,
            ),

            "dosage":
            dosage,
        })

        self.treatment_history = self.treatment_history[-128:]

        return report


cognitive_physician_engine = CognitivePhysicianEngine()
