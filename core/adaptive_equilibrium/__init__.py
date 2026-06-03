from core.adaptive_equilibrium.dynamic_equilibrium_engine import (
    DynamicEquilibriumEngine,
)
from core.adaptive_equilibrium.drift_assimilation import DriftAssimilation
from core.adaptive_equilibrium.contextual_topology_regulator import (
    ContextualTopologyRegulator,
)
from core.adaptive_equilibrium.adaptive_stability_cycles import (
    AdaptiveStabilityCycles,
)
from core.adaptive_equilibrium.resilient_identity_core import (
    ResilientIdentityCore,
)
from core.adaptive_equilibrium.semantic_balance_controller import (
    SemanticBalanceController,
)
from core.adaptive_equilibrium.propagation_stability_manager import (
    PropagationStabilityManager,
)
from core.adaptive_equilibrium.cognitive_recovery_engine import (
    CognitiveRecoveryEngine,
)
from core.adaptive_equilibrium.abstraction_priority_system import (
    AbstractionPrioritySystem,
)
from core.adaptive_equilibrium.flexible_constitutional_governance import (
    FlexibleConstitutionalGovernance,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class AdaptiveEquilibriumArchitecture:

    def __init__(self):

        self.dynamic_equilibrium_engine = DynamicEquilibriumEngine()
        self.drift_assimilation = DriftAssimilation()
        self.contextual_topology_regulator = ContextualTopologyRegulator()
        self.adaptive_stability_cycles = AdaptiveStabilityCycles()
        self.resilient_identity_core = ResilientIdentityCore()
        self.semantic_balance_controller = SemanticBalanceController()
        self.propagation_stability_manager = PropagationStabilityManager()
        self.cognitive_recovery_engine = CognitiveRecoveryEngine()
        self.abstraction_priority_system = AbstractionPrioritySystem()
        self.flexible_constitutional_governance = FlexibleConstitutionalGovernance()
        self.equilibrium_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        equilibrium = self.dynamic_equilibrium_engine.compute(context)
        drift = self.drift_assimilation.assimilate(context)
        topology = self.contextual_topology_regulator.regulate(context)
        cycles = self.adaptive_stability_cycles.plan(
            equilibrium,
            context.get("existential_pressure_report", {}),
        )
        identity = self.resilient_identity_core.reinforce(context)
        semantic = self.semantic_balance_controller.balance(context, drift)
        propagation = self.propagation_stability_manager.manage(context)
        abstraction = self.abstraction_priority_system.prioritize(
            context,
            equilibrium,
        )
        governance = self.flexible_constitutional_governance.govern(
            context,
            equilibrium,
            abstraction,
        )
        recovery = self.cognitive_recovery_engine.recover([
            cycles,
            identity,
            semantic,
            propagation,
        ])

        adaptive_score = _clamp(
            equilibrium.get("dynamic_equilibrium", 0.0) * 0.26
            +
            drift.get("assimilated_drift", 0.0) * 0.12
            +
            topology.get("contextual_topology_flexibility", 0.0) * 0.14
            +
            identity.get("identity_resilience", 0.0) * 0.18
            +
            semantic.get("semantic_balance", 0.0) * 0.16
            +
            propagation.get("propagation_stability", 0.0) * 0.14
        )

        policy = {
            "run_adaptive_stability_cycles":
            bool(cycles.get("planned_stability_cycles", [])),

            "assimilate_safe_drift":
            bool(drift.get("assimilation_actions", [])),

            "allow_limited_topology_adaptation":
            topology.get("topology_regulation_state")
            == "contextual_topology_adaptation_allowed",

            "constrain_abstraction_growth":
            abstraction.get("priority_state")
            == "abstraction_priority_constrained",

            "activate_equilibrium_recovery":
            bool(recovery.get("recovery_actions", [])),
        }

        report = {
            "system": "adaptive_equilibrium_architecture",
            "layer": "continuous_evolutionary_equilibrium",
            "dynamic_equilibrium": equilibrium,
            "drift_assimilation": drift,
            "contextual_topology_regulator": topology,
            "adaptive_stability_cycles": cycles,
            "resilient_identity_core": identity,
            "semantic_balance_controller": semantic,
            "propagation_stability_manager": propagation,
            "abstraction_priority_system": abstraction,
            "flexible_constitutional_governance": governance,
            "cognitive_recovery_engine": recovery,
            "adaptive_equilibrium_score": adaptive_score,
            "adaptive_equilibrium_policy": policy,
            "adaptive_equilibrium_state": (
                "adaptive_equilibrium_recovery_active"
                if policy["activate_equilibrium_recovery"]
                else "adaptive_equilibrium_stable"
            ),
        }

        self.equilibrium_history.append(report)
        self.equilibrium_history = self.equilibrium_history[-128:]

        return report


adaptive_equilibrium_architecture = AdaptiveEquilibriumArchitecture()


__all__ = [
    "AbstractionPrioritySystem",
    "AdaptiveEquilibriumArchitecture",
    "AdaptiveStabilityCycles",
    "CognitiveRecoveryEngine",
    "ContextualTopologyRegulator",
    "DriftAssimilation",
    "DynamicEquilibriumEngine",
    "FlexibleConstitutionalGovernance",
    "PropagationStabilityManager",
    "ResilientIdentityCore",
    "SemanticBalanceController",
    "adaptive_equilibrium_architecture",
]
