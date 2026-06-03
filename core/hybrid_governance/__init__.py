from core.hybrid_governance.paradigm_conflict_resolver import (
    ParadigmConflictResolver,
)
from core.hybrid_governance.hybrid_identity_balancer import (
    HybridIdentityBalancer,
)
from core.hybrid_governance.multi_modal_semantic_router import (
    MultiModalSemanticRouter,
)
from core.hybrid_governance.ontological_hybridization_control import (
    OntologicalHybridizationControl,
)
from core.hybrid_governance.structural_translation_regulator import (
    StructuralTranslationRegulator,
)
from core.hybrid_governance.adaptive_paradigm_firewall import (
    AdaptiveParadigmFirewall,
)
from core.hybrid_governance.hybrid_drift_absorption import (
    HybridDriftAbsorption,
)
from core.hybrid_governance.semantic_coexistence_engine import (
    SemanticCoexistenceEngine,
)
from core.hybrid_governance.cross_paradigm_alignment import (
    CrossParadigmAlignment,
)
from core.hybrid_governance.cognitive_fusion_stability import (
    CognitiveFusionStability,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class HybridGovernanceArchitecture:

    def __init__(self):

        self.paradigm_conflict_resolver = ParadigmConflictResolver()
        self.hybrid_identity_balancer = HybridIdentityBalancer()
        self.multi_modal_semantic_router = MultiModalSemanticRouter()
        self.ontological_hybridization_control = OntologicalHybridizationControl()
        self.structural_translation_regulator = StructuralTranslationRegulator()
        self.adaptive_paradigm_firewall = AdaptiveParadigmFirewall()
        self.hybrid_drift_absorption = HybridDriftAbsorption()
        self.semantic_coexistence_engine = SemanticCoexistenceEngine()
        self.cross_paradigm_alignment = CrossParadigmAlignment()
        self.cognitive_fusion_stability = CognitiveFusionStability()
        self.hybrid_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        conflict = self.paradigm_conflict_resolver.resolve(context)
        identity = self.hybrid_identity_balancer.balance(context, conflict)
        router = self.multi_modal_semantic_router.route(context, conflict)
        hybridization = self.ontological_hybridization_control.control(
            context,
            identity,
        )
        translation = self.structural_translation_regulator.regulate(
            context,
            router,
        )
        firewall = self.adaptive_paradigm_firewall.inspect(
            conflict,
            hybridization,
            translation,
        )
        absorption = self.hybrid_drift_absorption.absorb(context, conflict)
        coexistence = self.semantic_coexistence_engine.compute(
            identity,
            router,
            absorption,
        )
        alignment = self.cross_paradigm_alignment.align(
            conflict,
            coexistence,
            translation,
        )
        fusion = self.cognitive_fusion_stability.evaluate(
            alignment,
            hybridization,
            firewall,
        )

        hybrid_governance_score = _clamp(
            (1.0 - conflict.get("paradigm_conflict_score", 0.0)) * 0.18
            +
            identity.get("hybrid_identity_balance", 0.0) * 0.18
            +
            coexistence.get("semantic_coexistence", 0.0) * 0.20
            +
            alignment.get("alignment_score", 0.0) * 0.22
            +
            fusion.get("fusion_stability", 0.0) * 0.22
        )

        policy = {
            "require_cross_paradigm_attestation":
            bool(firewall.get("firewall_actions", [])),

            "sandbox_hybrid_fusion":
            fusion.get("fusion_state") == "hybrid_fusion_unstable",

            "route_multimodal_semantics":
            bool(router.get("semantic_routes", [])),

            "preserve_parallel_paradigms":
            coexistence.get("coexistence_state") == "semantic_coexistence_guarded",

            "regulate_structural_translation":
            bool(translation.get("translation_actions", [])),
        }

        report = {
            "system": "hybrid_governance_architecture",
            "layer": "cross_paradigm_coexistence_governance",
            "paradigm_conflict": conflict,
            "hybrid_identity_balance": identity,
            "multi_modal_semantic_router": router,
            "ontological_hybridization_control": hybridization,
            "structural_translation_regulator": translation,
            "adaptive_paradigm_firewall": firewall,
            "hybrid_drift_absorption": absorption,
            "semantic_coexistence": coexistence,
            "cross_paradigm_alignment": alignment,
            "cognitive_fusion_stability": fusion,
            "hybrid_governance_score": hybrid_governance_score,
            "hybrid_governance_policy": policy,
            "hybrid_governance_state": (
                "hybrid_governance_guarded"
                if any(policy.values())
                else "hybrid_governance_open"
            ),
        }

        self.hybrid_history.append(report)
        self.hybrid_history = self.hybrid_history[-128:]

        return report


hybrid_governance_architecture = HybridGovernanceArchitecture()


__all__ = [
    "AdaptiveParadigmFirewall",
    "CognitiveFusionStability",
    "CrossParadigmAlignment",
    "HybridDriftAbsorption",
    "HybridGovernanceArchitecture",
    "HybridIdentityBalancer",
    "MultiModalSemanticRouter",
    "OntologicalHybridizationControl",
    "ParadigmConflictResolver",
    "SemanticCoexistenceEngine",
    "StructuralTranslationRegulator",
    "hybrid_governance_architecture",
]
