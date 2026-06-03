from core.judicial_cognition.epistemic_court_engine import EpistemicCourtEngine
from core.judicial_cognition.ambiguity_reasoning_system import (
    AmbiguityReasoningSystem,
)
from core.judicial_cognition.sandboxed_cognitive_runtime import (
    SandboxedCognitiveRuntime,
)
from core.judicial_cognition.recursive_topology_judge import RecursiveTopologyJudge
from core.judicial_cognition.semantic_legality_validator import (
    SemanticLegalityValidator,
)
from core.judicial_cognition.causal_permission_controller import (
    CausalPermissionController,
)
from core.judicial_cognition.execution_gatekeeper import ExecutionGatekeeper
from core.judicial_cognition.reflective_argument_engine import (
    ReflectiveArgumentEngine,
)
from core.judicial_cognition.admissibility_filter import AdmissibilityFilter
from core.judicial_cognition.judicial_identity_supervisor import (
    JudicialIdentitySupervisor,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class JudicialCognitiveRuntime:

    def __init__(self):

        self.epistemic_court_engine = EpistemicCourtEngine()
        self.ambiguity_reasoning_system = AmbiguityReasoningSystem()
        self.sandboxed_cognitive_runtime = SandboxedCognitiveRuntime()
        self.recursive_topology_judge = RecursiveTopologyJudge()
        self.semantic_legality_validator = SemanticLegalityValidator()
        self.causal_permission_controller = CausalPermissionController()
        self.execution_gatekeeper = ExecutionGatekeeper()
        self.reflective_argument_engine = ReflectiveArgumentEngine()
        self.admissibility_filter = AdmissibilityFilter()
        self.judicial_identity_supervisor = JudicialIdentitySupervisor()
        self.judicial_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        court = self.epistemic_court_engine.review(context)
        ambiguity = self.ambiguity_reasoning_system.assess(context, court)
        sandbox = self.sandboxed_cognitive_runtime.assign(context, ambiguity, court)
        topology = self.recursive_topology_judge.judge(context)
        legality = self.semantic_legality_validator.validate(context, court)
        causal = self.causal_permission_controller.control(context, legality)
        gate = self.execution_gatekeeper.gate(
            court,
            sandbox,
            topology,
            legality,
            causal,
        )
        admissibility = self.admissibility_filter.filter(
            court,
            ambiguity,
            legality,
            causal,
        )
        arguments = self.reflective_argument_engine.build([
            court,
            ambiguity,
            sandbox,
            topology,
            legality,
            causal,
            gate,
            admissibility,
        ])
        supervisor = self.judicial_identity_supervisor.supervise([
            court,
            ambiguity,
            sandbox,
            topology,
            legality,
            causal,
            gate,
            admissibility,
        ])

        judicial_score = _clamp(
            court.get("court_score", 0.0) * 0.24
            +
            (1.0 - ambiguity.get("ambiguity_load", 1.0)) * 0.14
            +
            (1.0 - topology.get("recursive_topology_risk", 1.0)) * 0.16
            +
            legality.get("semantic_legality", 0.0) * 0.18
            +
            causal.get("causal_permission_score", 0.0) * 0.18
            +
            (0.10 if admissibility.get("admissible", False) else 0.0)
        )

        policy = {
            "require_epistemic_hearing":
            bool(court.get("court_actions", [])),

            "route_ambiguity_to_sandbox":
            bool(ambiguity.get("ambiguity_actions", [])),

            "sandbox_reasoning":
            sandbox.get("sandbox_required", False),

            "require_topology_judgement":
            bool(topology.get("topology_judgement_actions", [])),

            "validate_semantic_legality":
            bool(legality.get("legality_actions", [])),

            "require_causal_permission":
            bool(causal.get("causal_actions", [])),

            "block_or_sandbox_execution":
            gate.get("execution_permission") in ["blocked", "sandbox_only"],

            "filter_admissibility":
            admissibility.get("admissibility_state") != "claim_admissible",
        }

        report = {
            "system": "judicial_cognitive_runtime",
            "layer": "judicial_cognition",
            "epistemic_court": court,
            "ambiguity_reasoning": ambiguity,
            "sandboxed_runtime": sandbox,
            "recursive_topology_judge": topology,
            "semantic_legality": legality,
            "causal_permission": causal,
            "execution_gatekeeper": gate,
            "reflective_arguments": arguments,
            "admissibility_filter": admissibility,
            "judicial_identity_supervisor": supervisor,
            "judicial_score": judicial_score,
            "judicial_policy": policy,
            "judicial_state": (
                "judicial_cognition_active"
                if any(policy.values())
                else "judicial_cognition_clear"
            ),
        }

        self.judicial_history.append(report)
        self.judicial_history = self.judicial_history[-128:]

        return report


judicial_cognitive_runtime = JudicialCognitiveRuntime()


__all__ = [
    "AdmissibilityFilter",
    "AmbiguityReasoningSystem",
    "CausalPermissionController",
    "EpistemicCourtEngine",
    "ExecutionGatekeeper",
    "JudicialCognitiveRuntime",
    "JudicialIdentitySupervisor",
    "RecursiveTopologyJudge",
    "ReflectiveArgumentEngine",
    "SandboxedCognitiveRuntime",
    "SemanticLegalityValidator",
    "judicial_cognitive_runtime",
]
