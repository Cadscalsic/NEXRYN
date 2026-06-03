from core.cognitive_constitution.identity_compatibility_engine import (
    IdentityCompatibilityEngine,
)
from core.cognitive_constitution.semantic_admissibility_engine import (
    SemanticAdmissibilityEngine,
)
from core.cognitive_constitution.merge_legality_engine import (
    MergeLegalityEngine,
)
from core.cognitive_constitution.conflict_intensity_monitor import (
    ConflictIntensityMonitor,
)
from core.cognitive_constitution.layered_identity_overlap import (
    LayeredIdentityOverlap,
)
from core.cognitive_constitution.contradiction_prediction_engine import (
    ContradictionPredictionEngine,
)
from core.cognitive_constitution.semantic_constitutional_law import (
    SemanticConstitutionalLaw,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class CognitiveConstitutionLayer:

    def __init__(self):

        self.identity_compatibility_engine = IdentityCompatibilityEngine()
        self.semantic_admissibility_engine = SemanticAdmissibilityEngine()
        self.merge_legality_engine = MergeLegalityEngine()
        self.conflict_intensity_monitor = ConflictIntensityMonitor()
        self.layered_identity_overlap = LayeredIdentityOverlap()
        self.contradiction_prediction_engine = ContradictionPredictionEngine()
        self.semantic_constitutional_law = SemanticConstitutionalLaw()
        self.constitution_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):
            context = {}

        identity = self.identity_compatibility_engine.assess(context)
        semantic = self.semantic_admissibility_engine.assess(context)
        merge = self.merge_legality_engine.assess(
            context,
            identity,
            semantic,
        )
        conflict = self.conflict_intensity_monitor.assess(context)
        overlap = self.layered_identity_overlap.assess(context)
        contradiction = self.contradiction_prediction_engine.predict(
            context,
            identity,
            merge,
            conflict,
        )
        law = self.semantic_constitutional_law.rule(
            identity,
            semantic,
            merge,
            conflict,
            overlap,
            contradiction,
        )

        constitution_score = _clamp(
            law.get("constitutional_score", 0.0) * 0.34
            +
            identity.get("identity_compatibility", 0.0) * 0.16
            +
            semantic.get("semantic_admissibility", 0.0) * 0.14
            +
            merge.get("merge_legality", 0.0) * 0.14
            +
            overlap.get("layered_identity_overlap", 0.0) * 0.10
            +
            (1.0 - conflict.get("conflict_intensity", 1.0)) * 0.06
            +
            (1.0 - contradiction.get("contradiction_risk", 1.0)) * 0.06
        )

        policy = {
            "enforce_identity_compatibility":
            bool(identity.get("compatibility_actions", [])),

            "filter_semantic_admissibility":
            bool(semantic.get("admissibility_actions", [])),

            "block_illegal_merges":
            bool(merge.get("merge_legality_actions", [])),

            "reduce_conflict_intensity":
            bool(conflict.get("conflict_actions", [])),

            "preserve_layered_identity_boundaries":
            bool(overlap.get("overlap_actions", [])),

            "predict_contradictions_before_commit":
            bool(contradiction.get("contradiction_actions", [])),

            "enforce_semantic_constitutional_law":
            bool(law.get("constitutional_actions", [])),
        }

        report = {
            "system": "cognitive_constitution_layer",
            "layer": "cognitive_constitution",
            "identity_compatibility": identity,
            "semantic_admissibility": semantic,
            "merge_legality": merge,
            "conflict_intensity": conflict,
            "layered_identity_overlap": overlap,
            "contradiction_prediction": contradiction,
            "semantic_constitutional_law": law,
            "constitution_score": constitution_score,
            "cognitive_constitution_policy": policy,
            "constitution_state": (
                "cognitive_constitution_enforced"
                if any(policy.values())
                else "cognitive_constitution_clear"
            ),
        }

        self.constitution_history.append(report)
        self.constitution_history = self.constitution_history[-128:]

        return report


cognitive_constitution_layer = CognitiveConstitutionLayer()


__all__ = [
    "CognitiveConstitutionLayer",
    "ConflictIntensityMonitor",
    "ContradictionPredictionEngine",
    "IdentityCompatibilityEngine",
    "LayeredIdentityOverlap",
    "MergeLegalityEngine",
    "SemanticAdmissibilityEngine",
    "SemanticConstitutionalLaw",
    "cognitive_constitution_layer",
]
