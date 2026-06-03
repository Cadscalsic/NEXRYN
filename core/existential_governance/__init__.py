from core.existential_governance.epistemic_validation_engine import (
    EpistemicValidationEngine,
)
from core.existential_governance.survival_vs_truth_resolver import (
    SurvivalVsTruthResolver,
)
from core.existential_governance.semantic_legitimacy_controller import (
    SemanticLegitimacyController,
)
from core.existential_governance.long_term_extinction_memory import (
    LongTermExtinctionMemory,
)
from core.existential_governance.trust_weighted_reasoning import (
    TrustWeightedReasoning,
)
from core.existential_governance.existential_drift_balancer import (
    ExistentialDriftBalancer,
)
from core.existential_governance.continuity_ethics_engine import (
    ContinuityEthicsEngine,
)
from core.existential_governance.graph_governance_runtime import (
    GraphGovernanceRuntime,
)
from core.existential_governance.adaptive_semantic_judgement import (
    AdaptiveSemanticJudgement,
)
from core.existential_governance.persistent_identity_governor import (
    PersistentIdentityGovernor,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ExistentialGovernanceCore:

    def __init__(self):

        self.epistemic_validation_engine = EpistemicValidationEngine()
        self.survival_vs_truth_resolver = SurvivalVsTruthResolver()
        self.semantic_legitimacy_controller = SemanticLegitimacyController()
        self.long_term_extinction_memory = LongTermExtinctionMemory()
        self.trust_weighted_reasoning = TrustWeightedReasoning()
        self.existential_drift_balancer = ExistentialDriftBalancer()
        self.continuity_ethics_engine = ContinuityEthicsEngine()
        self.graph_governance_runtime = GraphGovernanceRuntime()
        self.adaptive_semantic_judgement = AdaptiveSemanticJudgement()
        self.persistent_identity_governor = PersistentIdentityGovernor()
        self.governance_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        epistemic = self.epistemic_validation_engine.validate(context)
        survival_truth = self.survival_vs_truth_resolver.resolve(context, epistemic)
        legitimacy = self.semantic_legitimacy_controller.control(context, epistemic)
        extinction_memory = self.long_term_extinction_memory.remember(context)
        trust_reasoning = self.trust_weighted_reasoning.weight(context, epistemic)
        drift = self.existential_drift_balancer.balance(context)
        ethics = self.continuity_ethics_engine.judge(context, survival_truth)
        graph = self.graph_governance_runtime.govern(context)
        judgement = self.adaptive_semantic_judgement.judge(
            epistemic,
            legitimacy,
            trust_reasoning,
            ethics,
        )
        identity_governor = self.persistent_identity_governor.govern([
            epistemic,
            survival_truth,
            legitimacy,
            extinction_memory,
            trust_reasoning,
            drift,
            ethics,
            graph,
            judgement,
        ])

        governance_score = _clamp(
            epistemic.get("epistemic_confidence", 0.0) * 0.18
            +
            survival_truth.get("truth_priority", 0.0) * 0.16
            +
            (1.0 - legitimacy.get("legitimacy_pressure", 1.0)) * 0.14
            +
            trust_reasoning.get("reasoning_weight", 0.0) * 0.14
            +
            (1.0 - drift.get("containment_need", 1.0)) * 0.12
            +
            ethics.get("continuity_ethics_score", 0.0) * 0.14
            +
            judgement.get("judgement_score", 0.0) * 0.12
        )

        policy = {
            "require_epistemic_attestation":
            bool(epistemic.get("validation_actions", [])),

            "block_survival_override_of_truth":
            bool(survival_truth.get("resolver_actions", [])),

            "route_semantics_to_legitimacy_review":
            bool(legitimacy.get("legitimacy_actions", [])),

            "preserve_extinction_memory":
            bool(extinction_memory.get("memory_actions", [])),

            "sandbox_low_trust_reasoning":
            bool(trust_reasoning.get("reasoning_actions", [])),

            "contain_existential_drift":
            bool(drift.get("drift_actions", [])),

            "require_continuity_ethics_review":
            bool(ethics.get("ethics_actions", [])),

            "govern_graph_propagation":
            bool(graph.get("graph_actions", [])),

            "defer_semantic_commit":
            judgement.get("judgement_state") == "adaptive_semantic_judgement_guarded",
        }

        report = {
            "system": "existential_governance_core",
            "layer": "truth_survival_continuity_governance",
            "epistemic_validation": epistemic,
            "survival_vs_truth": survival_truth,
            "semantic_legitimacy": legitimacy,
            "long_term_extinction_memory": extinction_memory,
            "trust_weighted_reasoning": trust_reasoning,
            "existential_drift": drift,
            "continuity_ethics": ethics,
            "graph_governance": graph,
            "adaptive_semantic_judgement": judgement,
            "persistent_identity_governor": identity_governor,
            "existential_governance_score": governance_score,
            "existential_governance_policy": policy,
            "existential_governance_state": (
                "existential_governance_active"
                if any(policy.values())
                else "existential_governance_clear"
            ),
        }

        self.governance_history.append(report)
        self.governance_history = self.governance_history[-128:]

        return report


existential_governance_core = ExistentialGovernanceCore()


__all__ = [
    "AdaptiveSemanticJudgement",
    "ContinuityEthicsEngine",
    "EpistemicValidationEngine",
    "ExistentialDriftBalancer",
    "ExistentialGovernanceCore",
    "GraphGovernanceRuntime",
    "LongTermExtinctionMemory",
    "PersistentIdentityGovernor",
    "SemanticLegitimacyController",
    "SurvivalVsTruthResolver",
    "TrustWeightedReasoning",
    "existential_governance_core",
]
