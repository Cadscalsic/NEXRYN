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
from core.knowledge.contextual_truth_support_policy import (
    ContextualTruthSupportPolicy,
)
from core.knowledge.identity_continuity_stabilization_policy import (
    IdentityContinuityStabilizationPolicy,
)


class IdentitySafeTruthIntegrationEngine:
    CONTEXTUAL_TRUTH_SUPPORT_THRESHOLD = (
        ContextualTruthSupportPolicy.SUPPORT_THRESHOLD
    )
    CONTEXTUAL_TRUTH_SUPPORT_GRACE = (
        ContextualTruthSupportPolicy.SUPPORT_GRACE
    )

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
        self.contextual_truth_support_policy = (
            ContextualTruthSupportPolicy()
        )
        self.identity_stabilization_policy = (
            IdentityContinuityStabilizationPolicy()
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
            or context.get(
                "identity_continuity_engine_report",
                {},
            ).get(
                "identity_continuity",
            )
            is not None
            or context.get(
                "identity_continuity_engine_report",
                {},
            ).get(
                "continuity_score",
            )
            is not None
        )

    def _context_hierarchy_supported(self, context):
        report = context.get("context_hierarchy", {})
        if not isinstance(report, dict):
            return True
        if report.get("hierarchy_required", False) is False:
            return True
        score = report.get(
            "context_hierarchy_score",
            report.get("score", 0.75),
        )
        return score >= 0.75

    def _contextual_truth_supported(self, context):
        authority = context.get("contextual_truth_authority", {})
        if not isinstance(authority, dict):
            authority = context.get(
                "contextual_truth",
                {},
            ).get("contextual_truth_authority", {})
        report = context.get("contextual_truth", {})
        report = report if isinstance(report, dict) else {}
        authority_score = (
            authority.get("contextual_truth_authority", 0.0)
            if isinstance(authority, dict)
            else 0.0
        )
        effective_score = max(
            report.get(
                "effective_contextual_truth",
                report.get("contextual_truth_score", 0.75),
            ),
            authority_score,
        )
        support = self.contextual_truth_support_policy.evaluate(
            contextual_truth=report,
            contextual_truth_authority=authority,
            context_hierarchy=context.get("context_hierarchy", {}),
            semantic_context=context.get("semantic_context", {}),
            effective_score=effective_score,
        )
        return support["contextual_truth_supported"]

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
            "causal_graph_alignment_supported":
            context.get(
                "causal_graph_alignment",
                {
                    "alignment_score": aggregate.causal_alignment,
                },
            ).get(
                "alignment_score",
                aggregate.causal_alignment,
            )
            >= self.minimum_causal_alignment,
            "causal_validation_supported":
            context.get(
                "causal_validation",
                {
                    "validation_score": self.minimum_causal_alignment,
                },
            ).get(
                "validation_score",
                self.minimum_causal_alignment,
            )
            >= 0.75,
            "contextual_truth_supported":
            self._contextual_truth_supported(context),
            "context_hierarchy_supported":
            self._context_hierarchy_supported(context),
            "semantic_context_supported":
            context.get(
                "semantic_context",
                {
                    "semantically_validated": True,
                },
            ).get(
                "semantically_validated",
                True,
            )
            is True,
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
        adaptive_contradiction = context.get(
            "adaptive_contradiction_governance",
            candidate.get("adaptive_contradiction_governance", {}),
        )
        stabilization_context = {
            **context,
            "concept": belief.concept,
            "truth_candidate": candidate,
            "adaptive_contradiction_governance":
            adaptive_contradiction,
        }
        observed_count = max(
            int(context.get(
                "knowledge_generalization",
                {},
            ).get("used_task_count", 0) or 0),
            int(adaptive_contradiction.get("observed_count", 0) or 0),
        )
        validation_count = max(
            int(context.get(
                "knowledge_generalization",
                {},
            ).get("validation_count", 0) or 0),
            int(adaptive_contradiction.get("validation_count", 0) or 0),
            observed_count if observed_count >= 8 else 0,
        )
        identity_continuity_stabilization = (
            self.identity_stabilization_policy.evaluate(
                checks,
                stabilization_context,
                concept=belief.concept,
                observed_count=observed_count,
                validation_count=validation_count,
            )
        )
        checks = identity_continuity_stabilization["adjusted_gates"]
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
            "identity_continuity_stabilization":
            identity_continuity_stabilization,
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
            "causal_graph_alignment":
            context.get("causal_graph_alignment", {}),
            "causal_explanation":
            context.get("causal_explanation", {}),
            "causal_validation":
            context.get("causal_validation", {}),
            "contextual_truth":
            context.get("contextual_truth", {}),
            "context_hierarchy":
            context.get("context_hierarchy", {}),
            "semantic_context":
            context.get("semantic_context", {}),
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
