from core.epistemic_models import BeliefState, TruthCommit
from core.epistemic_drift_regulator import (
    identity_continuity_score,
    semantic_drift_score,
)
from runtime.truth_gate_remediation_engine import TruthGateRemediationEngine
from core.knowledge.truth_state_authority import TruthStateAuthority
from core.identity.identity_governance_policy import (
    evaluate_identity_governance,
)
from core.knowledge.final_commit_decision_engine import (
    FinalCommitDecisionEngine,
)


class TruthCommitEngine:
    def __init__(
        self,
        minimum_evidence=3,
        minimum_trials=2,
        minimum_consistency=0.80,
        minimum_confidence=0.85,
        minimum_strength=0.80,
        maximum_contradiction=0.10,
    ):
        self.minimum_evidence = minimum_evidence
        self.minimum_trials = minimum_trials
        self.minimum_consistency = minimum_consistency
        self.minimum_confidence = minimum_confidence
        self.minimum_strength = minimum_strength
        self.maximum_contradiction = maximum_contradiction
        self.truth_registry = {}
        self.remediation_engine = TruthGateRemediationEngine()
        self.truth_state_authority = TruthStateAuthority()
        self.final_commit_decision_engine = FinalCommitDecisionEngine()

    def evaluate(self, belief, aggregate, trials, context=None):
        context = context if isinstance(context, dict) else {}
        passed_trials = sum(trial.trial_result.value == "PASSED" for trial in trials)
        semantic_stable = context.get("semantic_consistency", True) is not False
        rehearsal_safe = context.get("mutation_rehearsal_safe", True) is not False
        semantic_drift = semantic_drift_score(context)
        identity_continuity = identity_continuity_score(context)
        drift_regulation = context.get("epistemic_drift_regulation", {})
        identity_safe_truth_integration = context.get(
            "identity_safe_truth_integration",
            {},
        )
        adaptive_identity_integration = context.get(
            "adaptive_identity_integration_policy",
            {},
        )
        effective_maximum_semantic_drift = min(
            adaptive_identity_integration.get(
                "effective_maximum_semantic_drift",
                0.58,
            ),
            0.64,
        )
        effective_minimum_identity_continuity = max(
            adaptive_identity_integration.get(
                "effective_minimum_identity_continuity",
                0.62,
            ),
            0.59,
        )
        semantic_spine_recovery = context.get(
            "semantic_spine_recovery_report",
            {},
        )
        recovery_confirmed = (
            semantic_spine_recovery.get(
                "semantic_spine_recovery_confirmed",
                False,
            )
            is True
            and identity_safe_truth_integration.get(
                "integration_safe",
                False,
            )
            is True
        )
        if recovery_confirmed:
            recovered_semantic_drift = semantic_spine_recovery.get(
                "semantic_drift"
            )
            recovered_identity_continuity = semantic_spine_recovery.get(
                "identity_continuity"
            )
            if recovered_semantic_drift is not None:
                semantic_drift = recovered_semantic_drift
            if recovered_identity_continuity is not None:
                identity_continuity = recovered_identity_continuity
        allow_fragile_semantic_spine_integration = (
            identity_safe_truth_integration.get(
                "allow_fragile_semantic_spine_integration",
                False,
            )
            is True
        )
        identity_governance = identity_safe_truth_integration.get(
            "identity_governance",
        )
        if not isinstance(identity_governance, dict):
            identity_governance = evaluate_identity_governance(
                context,
                allow_fragile_semantic_spine_integration=
                allow_fragile_semantic_spine_integration,
                recovery_confirmed=recovery_confirmed,
            )
        identity_stable = identity_governance["identity_stable"]
        semantic_spine_stable = identity_governance[
            "semantic_spine_stable"
        ]

        gates = {
            "belief_is_truth_candidate":
            belief.state == BeliefState.TRUTH_CANDIDATE,

            "minimum_evidence": aggregate.evidence_count >= self.minimum_evidence,
            "minimum_trials": passed_trials >= self.minimum_trials,
            "minimum_consistency": aggregate.semantic_consistency >= self.minimum_consistency,
            "minimum_confidence": belief.confidence >= self.minimum_confidence,
            "minimum_strength": aggregate.evidence_strength >= self.minimum_strength,
            "contradiction_below_limit": aggregate.contradiction_score < self.maximum_contradiction,
            "identity_stable": identity_stable,
            "semantic_anchor_stable": semantic_stable,
            "semantic_spine_stable": semantic_spine_stable,
            "mutation_rehearsal_safe": rehearsal_safe,
            "semantic_drift_below_limit":
            semantic_drift < effective_maximum_semantic_drift,
            "identity_continuity_above_limit":
            identity_continuity >= effective_minimum_identity_continuity,
            "causal_spine_alignment":
            context.get(
                "causal_spine_alignment",
                {},
            ).get(
                "alignment_ready",
                True,
            )
            is True,
            "compatible_with_core_truths":
            context.get(
                "causal_spine_alignment",
                {},
            ).get(
                "compatible_with_core_truths",
                True,
            )
            is True,
            "causal_graph_validation":
            context.get(
                "causal_graph_validation",
                {},
            ).get(
                "validation_ready",
                True,
            )
            is True,
            "semantic_containment_inactive":
            identity_safe_truth_integration.get(
                "semantic_containment",
                {},
            ).get(
                "integration_allowed",
                True,
            )
            is True,
            "epistemic_drift_containment_inactive":
            identity_safe_truth_integration.get(
                "epistemic_drift_containment",
                {},
            ).get(
                "integration_allowed",
                (
                    not drift_regulation.get(
                        "truth_commit_blocked",
                        False,
                    )
                    or recovery_confirmed
                ),
            )
            is True,
        }
        identity_governance_gates = [
            "identity_stable",
            "semantic_spine_stable",
            "semantic_drift_below_limit",
            "identity_continuity_above_limit",
            "semantic_containment_inactive",
            "epistemic_drift_containment_inactive",
        ]
        failed_identity_governance_gates = [
            name
            for name in identity_governance_gates
            if not gates[name]
        ]
        recovery_state = semantic_spine_recovery.get("recovery_state")
        identity_governance_state = (
            "IDENTITY_GOVERNANCE_STABLE"
            if not failed_identity_governance_gates
            else "TEMPORARY_RECOVERY_HOLD"
            if recovery_state in [
                "REHEARSAL_VALIDATION_REQUIRED",
                "RECOVERY_MONITORING",
            ]
            else "IDENTITY_GOVERNANCE_REVIEW_REQUIRED"
        )
        previously_committed = belief.concept in self.truth_registry
        final_commit = self.final_commit_decision_engine.evaluate(
            gates,
            stable_truth_authority_locked=previously_committed,
            contradiction_score=aggregate.contradiction_score,
            truth_key=belief.concept,
        )
        decision = final_commit["decision"]
        committed = decision == "TRUTH_COMMITTED"
        reasons = list(final_commit["effective_failed_gates"])
        remediation = self.remediation_engine.build_plan(
            gates,
        )

        if committed:
            belief.state = BeliefState.TRUTH_COMMITTED
        elif previously_committed:
            belief.state = BeliefState.TRUTH_COMMITTED

        commit = TruthCommit(
            concept=belief.concept,
            decision=decision,
            committed=committed,
            reasons=reasons,
            belief_state=belief.state,
            evidence_strength=aggregate.evidence_strength,
            calibrated_confidence=belief.confidence,
            contradiction_score=aggregate.contradiction_score,
            trial_count=len(trials),
            constitutional_invariants={
                "survival_is_not_truth": True,
                "high_reputation_is_not_truth": True,
                "confidence_is_not_truth": True,
                "truth_requires_evidence": True,
                "truth_requires_trials": True,
                "truth_requires_validation": True,
            },
            metadata={
                "gates": gates,
                "semantic_drift": semantic_drift,
                "identity_continuity": identity_continuity,
                "identity_safe_truth_integration":
                identity_safe_truth_integration,
                "adaptive_identity_integration":
                adaptive_identity_integration,
                "effective_maximum_semantic_drift":
                effective_maximum_semantic_drift,
                "effective_minimum_identity_continuity":
                effective_minimum_identity_continuity,
                "semantic_spine_recovery":
                semantic_spine_recovery,
                "identity_governance":
                identity_governance,
                "identity_governance_state":
                identity_governance_state,
                "failed_identity_governance_gates":
                failed_identity_governance_gates,
                "causal_spine_alignment":
                context.get("causal_spine_alignment", {}),
                "causal_graph_validation":
                context.get("causal_graph_validation", {}),
                "remediation": remediation,
                "truth_state_authority": {
                    "truth_state_locked": previously_committed,
                    "forbid_automatic_truth_revocation":
                    previously_committed,
                },
                "final_commit_decision": final_commit,
            },
        )
        if committed:
            self.truth_registry[belief.concept] = commit
        return commit
