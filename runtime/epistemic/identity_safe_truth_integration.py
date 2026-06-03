from core.epistemic_drift_regulator import (
    identity_continuity_score,
    semantic_drift_score,
)
from core.identity.identity_continuity_engine import IdentityContinuityEngine
from core.identity.identity_governance_policy import (
    evaluate_identity_governance,
)
from runtime.identity.semantic_containment_engine import (
    SemanticContainmentEngine,
)
from runtime.identity.epistemic_drift_containment_engine import (
    EpistemicDriftContainmentEngine,
)


class IdentitySafeTruthIntegrationEngine:
    def __init__(
        self,
        minimum_causal_alignment=0.80,
        minimum_semantic_consistency=0.80,
        minimum_identity_continuity=0.62,
        maximum_semantic_drift=0.58,
    ):
        self.minimum_causal_alignment = minimum_causal_alignment
        self.minimum_semantic_consistency = minimum_semantic_consistency
        self.minimum_identity_continuity = minimum_identity_continuity
        self.maximum_semantic_drift = maximum_semantic_drift
        self.identity_continuity_engine = IdentityContinuityEngine(
            minimum_continuity=minimum_identity_continuity,
        )
        self.semantic_containment_engine = SemanticContainmentEngine()
        self.epistemic_drift_containment_engine = (
            EpistemicDriftContainmentEngine()
        )

    def _identity_delta(self, context):
        return context.get(
            "truth_candidate_identity_delta",
            context.get(
                "identity_safe_truth_integration",
                {},
            ).get(
                "identity_delta",
                0.0,
            ),
        )

    def _identity_continuity_observed(self, context):
        return (
            context.get("identity_continuity") is not None
            or context.get(
                "causal_rehearsal_report",
                {},
            ).get(
                "identity_forecaster",
                {},
            ).get(
                "identity_continuity",
            )
            is not None
            or context.get(
                "identity_continuity_guardian_report",
                {},
            ).get(
                "state_transition",
                {},
            ).get(
                "current_state",
                {},
            ).get(
                "identity_continuity",
            )
            is not None
        )

    def evaluate(self, belief, aggregate, candidate, context=None):
        context = context if isinstance(context, dict) else {}
        semantic_spine_recovery = context.get(
            "semantic_spine_recovery_report",
            {},
        )
        recovery_confirmed = semantic_spine_recovery.get(
            "semantic_spine_recovery_confirmed",
            False,
        ) is True
        identity_stability = context.get(
            "identity_stability_report",
            {},
        ).get(
            "identity_stability_state",
            "stable",
        )
        identity_continuity = identity_continuity_score(context)
        semantic_drift = semantic_drift_score(context)
        if recovery_confirmed:
            recovered_identity_continuity = semantic_spine_recovery.get(
                "identity_continuity"
            )
            recovered_semantic_drift = semantic_spine_recovery.get(
                "semantic_drift"
            )
            if recovered_identity_continuity is not None:
                identity_continuity = recovered_identity_continuity
            if recovered_semantic_drift is not None:
                semantic_drift = recovered_semantic_drift
        identity_delta = self._identity_delta(context)
        adaptive_policy = context.get(
            "adaptive_identity_integration_policy",
            {},
        )
        maximum_semantic_drift = adaptive_policy.get(
            "effective_maximum_semantic_drift",
            self.maximum_semantic_drift,
        )
        minimum_identity_continuity = adaptive_policy.get(
            "effective_minimum_identity_continuity",
            self.minimum_identity_continuity,
        )
        identity_integration_reward = adaptive_policy.get(
            "identity_integration_reward",
            0.0,
        )
        identity_continuity_observed = (
            self._identity_continuity_observed(context)
            or recovery_confirmed
        )
        identity_continuity_report = self.identity_continuity_engine.evaluate(
            belief.concept,
            identity_continuity,
            identity_delta,
            minimum_identity_continuity,
            context.get("truth_candidate_breaks_core_truths", False),
        )
        semantic_containment = self.semantic_containment_engine.evaluate(
            belief.concept,
            context,
        )
        epistemic_drift_containment = (
            self.epistemic_drift_containment_engine.evaluate(
                context,
                recovery_confirmed=recovery_confirmed,
            )
        )
        checks = {
            "truth_candidate_ready":
            candidate.get("eligible_for_truth_candidate", False),
            "causal_alignment_supported":
            aggregate.causal_alignment >= self.minimum_causal_alignment,
            "semantic_consistency_supported":
            aggregate.semantic_consistency
            >= self.minimum_semantic_consistency,
            "identity_continuity_preserved":
            identity_continuity_observed
            and identity_continuity_report["allowed_transition"],
            "identity_not_degrading": identity_delta >= 0.0,
            "semantic_drift_below_limit":
            semantic_drift < maximum_semantic_drift,
            "mutation_rehearsal_safe":
            context.get("mutation_rehearsal_safe", True) is not False,
            "identity_repair_inactive":
            recovery_confirmed
            or identity_stability not in [
                "rollback_required",
                "recovery_monitoring",
            ],
            "semantic_containment_inactive":
            semantic_containment["integration_allowed"],
            "epistemic_drift_containment_inactive":
            epistemic_drift_containment["integration_allowed"],
        }
        fragile_semantic_spine = (
            identity_stability == "fragile_semantic_spine"
        )
        base_integration_safe = all(checks.values())
        allow_fragile_semantic_spine_integration = (
            fragile_semantic_spine
            and base_integration_safe
        )
        identity_governance = evaluate_identity_governance(
            context,
            allow_fragile_semantic_spine_integration=
            allow_fragile_semantic_spine_integration,
            recovery_confirmed=recovery_confirmed,
        )
        checks.update({
            "identity_stable":
            identity_governance["identity_stable"],
            "semantic_spine_stable":
            identity_governance["semantic_spine_stable"],
        })
        integration_safe = all(checks.values())
        strengthens_identity = integration_safe and (
            fragile_semantic_spine
            or identity_delta > 0.0
            or identity_integration_reward > 0.0
        )

        return {
            "system": "identity_safe_truth_integration_engine",
            "concept": belief.concept,
            "integration_state": (
                "IDENTITY_REINFORCING_TRUTH"
                if strengthens_identity
                else "IDENTITY_SAFE_TRUTH"
                if integration_safe
                else "AWAITING_TRUTH_CANDIDATE"
                if not checks["truth_candidate_ready"]
                else "HOLD_FOR_IDENTITY_SAFETY"
            ),
            "integration_safe": integration_safe,
            "strengthens_identity": strengthens_identity,
            "allow_fragile_semantic_spine_integration":
            fragile_semantic_spine and strengthens_identity,
            "identity_governance": identity_governance,
            "identity_stability_state": identity_stability,
            "identity_continuity": identity_continuity,
            "identity_continuity_observed": identity_continuity_observed,
            "identity_delta": identity_delta,
            "identity_continuity_forecast": identity_continuity_report,
            "semantic_containment": semantic_containment,
            "epistemic_drift_containment":
            epistemic_drift_containment,
            "semantic_consistency": aggregate.semantic_consistency,
            "causal_alignment": aggregate.causal_alignment,
            "semantic_drift": semantic_drift,
            "effective_maximum_semantic_drift":
            maximum_semantic_drift,
            "effective_minimum_identity_continuity":
            minimum_identity_continuity,
            "identity_integration_reward": identity_integration_reward,
            "adaptive_identity_integration_policy": adaptive_policy,
            "semantic_spine_recovery_confirmed": recovery_confirmed,
            "checks": checks,
            "failed_checks": [
                name
                for name, passed in checks.items()
                if not passed
            ],
            "automatic_identity_safety_bypass_forbidden": True,
        }


__all__ = [
    "IdentitySafeTruthIntegrationEngine",
]
