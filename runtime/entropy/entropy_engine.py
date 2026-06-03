# ============================================
# NEXRYN COGNITIVE ENTROPY ENGINE
# ============================================

from datetime import datetime


class CognitiveEntropyEngine:

    def __init__(self):

        self.entropy_history = []

    def compute_runtime_entropy(self, context):

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        memory = context.get(
            "hierarchical_memory_architecture_report",
            {}
        )

        folding = context.get(
            "safe_concept_folding_report",
            {}
        )

        semantic = context.get(
            "semantic_activation_report",
            {}
        )

        projected_entropy = (
            governance.get(
                "signals",
                {}
            )
            .get(
                "projected_entropy",
                0
            )
        )

        return round(
            min(
                min(
                    projected_entropy / 12,
                    1.0
                )
                * 0.35
                +
                memory.get(
                    "combined_memory_pressure",
                    0.0
                )
                * 0.25
                +
                folding.get(
                    "folding_pressure",
                    0.0
                )
                * 0.25
                +
                semantic.get(
                    "semantic_temperature",
                    0.0
                )
                * 0.15,
                1.0
            ),
            4
        )

    def detect_semantic_fragmentation(self, context):

        pointer_report = context.get(
            "semantic_pointer_report",
            {}
        )

        pointer_count = pointer_report.get(
            "pointer_count",
            0
        )

        alias_count = pointer_report.get(
            "alias_count",
            0
        )

        fragmentation = round(
            min(
                pointer_count
                /
                max(
                    alias_count,
                    1
                ),
                1.0
            ),
            4
        )

        return {
            "semantic_fragmentation":
            fragmentation,

            "fragmentation_state":
            (
                "fragmented"
                if fragmentation >= 0.80
                else "contained"
            )
        }

    def regulate_ontology_pressure(self, context):

        governance = context.get(
            "cognitive_governance_report",
            {}
        )

        ontology_pressure = (
            governance.get(
                "signals",
                {}
            )
            .get(
                "ontology_pressure",
                0.0
            )
        )

        return (
            "compress_without_identity_loss"
            if ontology_pressure >= 0.65
            else "observe_ontology"
        )

    def stabilize_runtime(self, entropy):

        if entropy >= 0.70:

            return [
                "freeze_unstable_merges",
                "reduce_symbolic_mutation",
                "compress_background_context"
            ]

        if entropy >= 0.50:

            return [
                "reduce_symbolic_mutation"
            ]

        return []

    def inject_safe_novelty(self, entropy):

        return (
            entropy < 0.35
        )

    def run_cycle(self, context):

        entropy = self.compute_runtime_entropy(
            context
        )

        fragmentation = self.detect_semantic_fragmentation(
            context
        )

        report = {
            "engine":
            "cognitive_entropy",

            "runtime_entropy":
            entropy,

            "entropy_state":
            (
                "critical"
                if entropy >= 0.70
                else "elevated"
                if entropy >= 0.50
                else "stable"
            ),

            "semantic_fragmentation":
            fragmentation,

            "ontology_policy":
            self.regulate_ontology_pressure(
                context
            ),

            "stabilization_actions":
            self.stabilize_runtime(
                entropy
            ),

            "safe_novelty_allowed":
            self.inject_safe_novelty(
                entropy
            ),

            "timestamp":
            str(
                datetime.utcnow()
            )
        }

        self.entropy_history.append(
            report
        )

        self.entropy_history = (
            self.entropy_history[-32:]
        )

        return report


cognitive_entropy_engine = (
    CognitiveEntropyEngine()
)
