# ============================================
# NEXRYN COGNITIVE HEALTH SYMPTOM ANALYSIS
# ============================================

from core.cognitive_health.diagnostic_models import (
    clamp,
)


class SymptomAnalyzer:

    def analyze(self, metrics):

        symptoms = []

        rules = [
            ("cognitive_fever", "cognitive_fever_score", 0.62),
            ("semantic_entropy", "semantic_entropy", 0.66),
            ("identity_drift", "identity_drift", 0.48),
            ("recursive_pressure", "recursion_pressure", 0.70),
            ("ontology_fragmentation", "ontology_fragmentation", 0.58),
            ("memory_congestion", "memory_pressure", 0.72),
            ("semantic_noise", "semantic_noise", 0.62),
            ("exploration_overload", "exploration_overload", 0.64),
            ("merge_exhaustion", "merge_exhaustion", 0.55),
            ("anchor_weakness", "semantic_anchor_integrity", 0.42),
            ("constitutional_instability", "constitutional_stability", 0.50),
            ("topology_stress", "topology_integrity", 0.45),
        ]

        for name, key, threshold in rules:

            value = metrics.get(
                key,
                0.0,
            )

            if key in [
                "semantic_anchor_integrity",
                "constitutional_stability",
                "topology_integrity",
            ]:

                active = value <= threshold
                intensity = clamp(
                    1.0 - value,
                )

            else:

                active = value >= threshold
                intensity = value

            if active:

                symptoms.append({
                    "symptom":
                    name,

                    "metric":
                    key,

                    "intensity":
                    clamp(
                        intensity,
                    ),
                })

        return {
            "system":
            "symptom_analysis",

            "symptoms":
            symptoms,

            "symptom_count":
            len(
                symptoms,
            ),

            "symptom_load":
            clamp(
                sum(
                    item.get(
                        "intensity",
                        0.0,
                    )
                    for item in symptoms
                )
                /
                max(
                    len(
                        symptoms,
                    ),
                    1,
                )
            ),
        }
