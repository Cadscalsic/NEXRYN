from core.existential_homeostasis.adaptive_stability_regulator import (
    AdaptiveStabilityRegulator,
)
from core.existential_homeostasis.semantic_equilibrium_engine import (
    SemanticEquilibriumEngine,
)
from core.existential_homeostasis.identity_homeostasis import (
    IdentityHomeostasis,
)
from core.existential_homeostasis.invariant_recycling_system import (
    InvariantRecyclingSystem,
)
from core.existential_homeostasis.drift_recovery_loops import (
    DriftRecoveryLoops,
)
from core.existential_homeostasis.ontological_pressure_balancer import (
    OntologicalPressureBalancer,
)
from core.existential_homeostasis.semantic_gravity_engine import (
    SemanticGravityEngine,
)
from core.existential_homeostasis.evolutionary_recovery_cycles import (
    EvolutionaryRecoveryCycles,
)
from core.existential_homeostasis.continuity_equilibrium import (
    ContinuityEquilibrium,
)
from core.existential_homeostasis.adaptive_self_preservation import (
    AdaptiveSelfPreservation,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(max(minimum, min(value, maximum)), 4)


class ExistentialHomeostasisSystem:

    def __init__(self):

        self.adaptive_stability_regulator = AdaptiveStabilityRegulator()
        self.semantic_equilibrium_engine = SemanticEquilibriumEngine()
        self.identity_homeostasis = IdentityHomeostasis()
        self.invariant_recycling_system = InvariantRecyclingSystem()
        self.drift_recovery_loops = DriftRecoveryLoops()
        self.ontological_pressure_balancer = OntologicalPressureBalancer()
        self.semantic_gravity_engine = SemanticGravityEngine()
        self.evolutionary_recovery_cycles = EvolutionaryRecoveryCycles()
        self.continuity_equilibrium = ContinuityEquilibrium()
        self.adaptive_self_preservation = AdaptiveSelfPreservation()
        self.homeostasis_history = []

    def run_cycle(self, context):

        if not isinstance(context, dict):

            context = {}

        stability = self.adaptive_stability_regulator.regulate(context)
        semantic = self.semantic_equilibrium_engine.compute(context)
        identity = self.identity_homeostasis.balance(context)
        recycling = self.invariant_recycling_system.recycle(context)
        drift = self.drift_recovery_loops.recover(context)
        pressure = self.ontological_pressure_balancer.balance(context)
        gravity = self.semantic_gravity_engine.compute(context, semantic)
        recovery = self.evolutionary_recovery_cycles.plan(
            stability,
            pressure,
            recycling,
        )
        continuity = self.continuity_equilibrium.compute(
            identity,
            semantic,
            context.get("existential_economics_report", {}),
        )

        preservation = self.adaptive_self_preservation.preserve([
            stability,
            semantic,
            identity,
            drift,
            pressure,
            gravity,
            recovery,
        ])

        homeostasis_score = _clamp(
            stability.get("stability_demand", 0.0) * 0.18
            +
            semantic.get("semantic_equilibrium", 0.0) * 0.22
            +
            identity.get("identity_balance", 0.0) * 0.22
            +
            (1.0 - pressure.get("balanced_pressure", 0.0)) * 0.18
            +
            continuity.get("continuity_equilibrium", 0.0) * 0.20
        )

        policy = {
            "prioritize_stability_cycles":
            bool(stability.get("regulator_actions", [])),

            "increase_semantic_gravity":
            bool(gravity.get("gravity_actions", [])),

            "run_drift_recovery":
            bool(drift.get("recovery_loops", [])),

            "recycle_critical_invariants":
            bool(recycling.get("recycled_invariants", [])),

            "pause_expansion_for_recovery":
            pressure.get("balanced_pressure", 0.0) >= 0.58,
        }

        report = {
            "system": "existential_homeostasis_system",
            "layer": "long_term_evolutionary_homeostasis",
            "adaptive_stability_regulator": stability,
            "semantic_equilibrium": semantic,
            "identity_homeostasis": identity,
            "invariant_recycling": recycling,
            "drift_recovery_loops": drift,
            "ontological_pressure_balancer": pressure,
            "semantic_gravity": gravity,
            "evolutionary_recovery_cycles": recovery,
            "continuity_equilibrium": continuity,
            "adaptive_self_preservation": preservation,
            "existential_homeostasis_score": homeostasis_score,
            "homeostasis_policy": policy,
            "existential_homeostasis_state": (
                "existential_homeostasis_repairing"
                if any(policy.values())
                else "existential_homeostasis_balanced"
            ),
        }

        self.homeostasis_history.append(report)
        self.homeostasis_history = self.homeostasis_history[-128:]

        return report


existential_homeostasis_system = ExistentialHomeostasisSystem()


__all__ = [
    "AdaptiveSelfPreservation",
    "AdaptiveStabilityRegulator",
    "ContinuityEquilibrium",
    "DriftRecoveryLoops",
    "EvolutionaryRecoveryCycles",
    "ExistentialHomeostasisSystem",
    "IdentityHomeostasis",
    "InvariantRecyclingSystem",
    "OntologicalPressureBalancer",
    "SemanticEquilibriumEngine",
    "SemanticGravityEngine",
    "existential_homeostasis_system",
]
