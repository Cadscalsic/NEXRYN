from core.ontological_stability.invariant_boundary_engine import (
    InvariantBoundaryEngine,
    InvariantLevel,
)
from core.ontological_stability.semantic_spine_protection import (
    SemanticSpineProtectionEngine,
)
from core.ontological_stability.identity_boundary_system import (
    IdentityBoundarySystem,
)
from core.ontological_stability.contextual_negotiation_limits import (
    ContextualNegotiationLimits,
)
from core.ontological_stability.existential_constraints import (
    ExistentialConstraints,
)
from core.ontological_stability.adaptive_vs_absolute_balance import (
    AdaptiveVsAbsoluteBalance,
)
from core.ontological_stability.topology_integrity_guard import (
    TopologyIntegrityGuard,
)
from core.ontological_stability.invariant_survival_engine import (
    InvariantSurvivalEngine,
)
from core.ontological_stability.contextual_limiters import (
    ContextualLimiters,
)
from core.ontological_stability.continuity_locking import (
    ContinuityLocking,
)
from core.ontological_stability.ontological_recovery import (
    OntologicalRecovery,
)


def _clamp(value, minimum=0.0, maximum=1.0):

    try:
        value = float(value)
    except Exception:
        value = minimum

    return round(
        max(
            minimum,
            min(value, maximum),
        ),
        4,
    )


class OntologicalBoundarySystem:

    def __init__(self):

        self.invariant_boundary_engine = InvariantBoundaryEngine()
        self.semantic_spine_protection = SemanticSpineProtectionEngine()
        self.identity_boundary_system = IdentityBoundarySystem()
        self.contextual_negotiation_limits = ContextualNegotiationLimits()
        self.existential_constraints = ExistentialConstraints()
        self.balance_engine = AdaptiveVsAbsoluteBalance()
        self.topology_integrity_guard = TopologyIntegrityGuard()
        self.invariant_survival_engine = InvariantSurvivalEngine()
        self.contextual_limiters = ContextualLimiters()
        self.continuity_locking = ContinuityLocking()
        self.ontological_recovery = OntologicalRecovery()

    def existential_fatigue(self, context, spine_report, identity_report):

        graveyard_pressure = (
            context.get(
                "evolutionary_graveyard_report",
                {},
            )
            .get(
                "graveyard_pressure",
                {},
            )
            .get(
                "pressure_score",
                0.0,
            )
        )

        identity_stress = _clamp(
            identity_report.get(
                "blocked_identity_fusions",
                0,
            )
            * 0.18
        )

        contextual_pressure = _clamp(
            len(
                context.get(
                    "proposed_contextual_negotiations",
                    [],
                )
            )
            * 0.12
        )

        semantic_liquidity = _clamp(
            1.0
            -
            spine_report.get(
                "spine_stability",
                0.0,
            )
        )

        invariant_erosion = _clamp(
            context.get(
                "extinction_engine_report",
                {},
            ).get(
                "extinct_count",
                0,
            )
            * 0.14
        )

        fatigue = _clamp(
            graveyard_pressure * 0.24
            +
            identity_stress * 0.22
            +
            contextual_pressure * 0.14
            +
            semantic_liquidity * 0.24
            +
            invariant_erosion * 0.16
        )

        return {
            "system":
            "existential_fatigue_monitoring",

            "ontological_fatigue":
            fatigue,

            "identity_stress":
            identity_stress,

            "contextual_pressure":
            contextual_pressure,

            "semantic_liquidity":
            semantic_liquidity,

            "invariant_erosion":
            invariant_erosion,

            "fatigue_state":
            (
                "existential_fatigue_high"
                if fatigue >= 0.56
                else "existential_fatigue_elevated"
                if fatigue >= 0.32
                else "existential_fatigue_contained"
            ),
        }

    def run_cycle(self, context):

        if not isinstance(
            context,
            dict,
        ):

            context = {}

        invariant_report = self.invariant_boundary_engine.run_cycle(
            context,
        )
        spine_report = self.semantic_spine_protection.run_cycle(
            context,
        )
        identity_report = self.identity_boundary_system.run_cycle(
            context,
        )
        negotiation_report = self.contextual_negotiation_limits.run_cycle(
            context,
        )
        constraints_report = self.existential_constraints.run_cycle(
            context,
            invariant_report,
        )
        balance_report = self.balance_engine.run_cycle(
            invariant_report,
            negotiation_report,
        )
        topology_report = self.topology_integrity_guard.run_cycle(
            context,
        )
        survival_report = self.invariant_survival_engine.run_cycle(
            context,
        )
        fatigue_report = self.existential_fatigue(
            context,
            spine_report,
            identity_report,
        )
        limiter_report = self.contextual_limiters.run_cycle(
            negotiation_report,
            fatigue_report,
        )
        continuity_report = self.continuity_locking.run_cycle(
            spine_report,
            identity_report,
        )
        recovery_report = self.ontological_recovery.run_cycle(
            spine_report,
            identity_report,
            survival_report,
            fatigue_report,
        )

        freeze_high_risk = (
            spine_report.get(
                "fragile_semantic_spine",
                False,
            )
            or identity_report.get(
                "blocked_identity_fusions",
                0,
            )
            > 0
            or fatigue_report.get(
                "ontological_fatigue",
                0.0,
            )
            >= 0.56
        )

        policy = {
            "freeze_new_fusions":
            freeze_high_risk,

            "freeze_high_risk_mutations":
            freeze_high_risk,

            "reduce_merge_pressure":
            spine_report.get(
                "fragile_semantic_spine",
                False,
            )
            or identity_report.get(
                "blocked_identity_fusions",
                0,
            )
            > 0,

            "increase_temporal_validation":
            freeze_high_risk,

            "pause_large_scale_evolution":
            fatigue_report.get(
                "ontological_fatigue",
                0.0,
            )
            >= 0.56,
        }

        return {
            "system":
            "ontological_boundary_system",

            "layer":
            "contextual_existential_stabilization",

            "invariant_boundary":
            invariant_report,

            "semantic_spine_protection":
            spine_report,

            "identity_boundary":
            identity_report,

            "contextual_negotiation_limits":
            negotiation_report,

            "existential_constraints":
            constraints_report,

            "adaptive_vs_absolute_balance":
            balance_report,

            "topology_integrity_guard":
            topology_report,

            "invariant_survival":
            survival_report,

            "existential_fatigue":
            fatigue_report,

            "contextual_limiters":
            limiter_report,

            "continuity_locking":
            continuity_report,

            "ontological_recovery":
            recovery_report,

            "ontological_policy":
            policy,

            "ontological_stability_state":
            (
                "existential_stabilization_active"
                if any(
                    policy.values(),
                )
                else "ontological_boundaries_stable"
            ),
        }


ontological_boundary_system = OntologicalBoundarySystem()


__all__ = [
    "AdaptiveVsAbsoluteBalance",
    "ContextualLimiters",
    "ContextualNegotiationLimits",
    "ContinuityLocking",
    "ExistentialConstraints",
    "IdentityBoundarySystem",
    "InvariantBoundaryEngine",
    "InvariantLevel",
    "InvariantSurvivalEngine",
    "OntologicalBoundarySystem",
    "OntologicalRecovery",
    "SemanticSpineProtectionEngine",
    "TopologyIntegrityGuard",
    "ontological_boundary_system",
]
