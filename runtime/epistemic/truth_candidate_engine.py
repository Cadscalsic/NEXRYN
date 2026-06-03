from core.epistemic_models import BeliefState
from core.knowledge.contradiction_review_policy import (
    SOFT_REVIEW_ZONE,
    classify_contradiction_review,
)
from core.knowledge.truth_state_authority import TruthStateAuthority
from runtime.causal import RuntimeCausalAlignmentEngine


class TruthCandidateEngine:
    MINIMUM_INDEPENDENT_TASKS = 8
    CONTRADICTION_REVIEW_ZONE = SOFT_REVIEW_ZONE

    METRICS = [
        {
            "name": "evidence_strength",
            "comparator": ">=",
            "threshold": 0.80,
            "action": "collect_execution_validation_evidence",
        },
        {
            "name": "confidence",
            "comparator": ">=",
            "threshold": 0.85,
            "action": "reinforce_reliable_independent_evidence",
        },
        {
            "name": "contradiction_score",
            "comparator": "<",
            "threshold": 0.10,
            "action": "resolve_or_explain_contradictory_evidence",
        },
        {
            "name": "causal_alignment",
            "comparator": ">=",
            "threshold": 0.80,
            "action": "collect_causal_attestation_evidence",
        },
    ]

    def __init__(self):
        self.truth_state_authority = TruthStateAuthority()
        self.runtime_causal_alignment_engine = (
            RuntimeCausalAlignmentEngine()
        )

    def _metric(self, concept, specification, current_value):
        threshold = specification["threshold"]
        comparator = specification["comparator"]
        passed = (
            current_value >= threshold
            if comparator == ">="
            else current_value < threshold
        )
        gap = (
            max(threshold - current_value, 0.0)
            if comparator == ">="
            else max(current_value - threshold, 0.0)
        )
        return {
            "concept": concept,
            "metric": specification["name"],
            "current_value": current_value,
            "threshold": {
                "comparator": comparator,
                "required": threshold,
            },
            "gap": round(gap, 4),
            "passed": passed,
            "status": "PASSED" if passed else "FAILED",
            "required_action": None if passed else specification["action"],
        }

    def _semantic_spine_recovery(self, context):
        semantic_spine = context.get(
            "semantic_spine_report",
            {},
        )
        semantic_anchor = context.get(
            "semantic_anchor_graph_report",
            context.get(
                "identity_continuity_guardian_report",
                {},
            ).get(
                "semantic_anchor_graph",
                {},
            ),
        ).get(
            "identity_stability",
            {},
        )
        report = semantic_spine or semantic_anchor
        state = report.get(
            "semantic_spine_state",
            report.get(
                "stability_state",
                "unknown",
            ),
        )
        recovery_streak = report.get("recovery_streak", 0)
        required_cycles = report.get("required_recovery_cycles", 3)
        recovery_pending = state == "semantic_spine_recovering"

        return {
            "stability_state": state,
            "recovery_streak": recovery_streak,
            "required_recovery_cycles": required_cycles,
            "remaining_recovery_cycles": (
                max(required_cycles - recovery_streak, 0)
                if recovery_pending
                else 0
            ),
            "recovery_confirmation_pending": recovery_pending,
        }

    def _contradiction_review(self, contradiction_score):
        threshold = next(
            item["threshold"]
            for item in self.METRICS
            if item["name"] == "contradiction_score"
        )
        review = classify_contradiction_review(
            contradiction_score,
            threshold=threshold,
            soft_review_zone=self.CONTRADICTION_REVIEW_ZONE,
        )
        return {
            "effective_contradiction_score": contradiction_score,
            "contradiction_threshold": threshold,
            "contradiction_review_zone":
            self.CONTRADICTION_REVIEW_ZONE,
            **review,
        }

    def evaluate(self, belief, aggregate, context=None):
        context = context if isinstance(context, dict) else {}
        causal_boundary_alignment = context.get(
            "causal_boundary_alignment",
        )
        if not isinstance(causal_boundary_alignment, dict):
            causal_boundary_alignment = (
                self.runtime_causal_alignment_engine.evaluate(
                    belief.concept,
                    aggregate,
                    context,
                )
            )
        raw_contradiction_score = aggregate.contradiction_score
        effective_contradiction_score = causal_boundary_alignment[
            "adjusted_contradiction_score"
        ]
        contradiction_review = self._contradiction_review(
            effective_contradiction_score,
        )
        if belief.state == BeliefState.TRUTH_COMMITTED:
            return {
                "system": "truth_candidate_engine",
                "concept": belief.concept,
                "current_state": belief.state.value,
                "candidate_state": "TRUTH_STATE_LOCKED",
                "validated_knowledge": True,
                "qualified_metrics": True,
                "stage_eligible_for_truth_candidate": True,
                "metrics_eligible_for_truth_candidate": True,
                "eligible_for_truth_candidate": True,
                "eligibility_reason": "stable_truth_authority_locked",
                "metric_progress": {
                    "passed_count": 0,
                    "required_count": 0,
                    "progress_ratio": 1.0,
                },
                "metrics": [],
                "blocked_metrics": [],
                "ranked_bottlenecks": [],
                "dominant_bottleneck": None,
                "required_actions": [],
                **contradiction_review,
                "raw_contradiction_score": raw_contradiction_score,
                "causal_boundary_alignment":
                causal_boundary_alignment,
                "semantic_spine_recovery":
                self._semantic_spine_recovery(context),
                "minimum_independent_tasks":
                self.MINIMUM_INDEPENDENT_TASKS,
                "automatic_truth_commit_forbidden": True,
                "truth_candidate_evaluation_skipped": True,
                "truth_state_authority": {
                    "state": "TRUTH_COMMITTED",
                    "truth_state_locked": True,
                },
            }
        generalization = context.get("knowledge_generalization", {})
        values = {
            "evidence_strength": aggregate.evidence_strength,
            "confidence": belief.confidence,
            "contradiction_score": effective_contradiction_score,
            "causal_alignment": aggregate.causal_alignment,
        }
        metrics = [
            self._metric(
                belief.concept,
                specification,
                values[specification["name"]],
            )
            for specification in self.METRICS
        ]
        used_task_count = generalization.get("used_task_count", 0)
        if used_task_count:
            metrics.append({
                "concept": belief.concept,
                "metric": "independent_task_coverage",
                "current_value": used_task_count,
                "threshold": {
                    "comparator": ">=",
                    "required": self.MINIMUM_INDEPENDENT_TASKS,
                },
                "gap": max(
                    self.MINIMUM_INDEPENDENT_TASKS - used_task_count,
                    0,
                ),
                "passed":
                used_task_count >= self.MINIMUM_INDEPENDENT_TASKS,
                "status": (
                    "PASSED"
                    if used_task_count >= self.MINIMUM_INDEPENDENT_TASKS
                    else "FAILED"
                ),
                "required_action": (
                    None
                    if used_task_count >= self.MINIMUM_INDEPENDENT_TASKS
                    else "collect_independent_cross_task_replications"
                ),
            })
        blocked_metrics = [
            item["metric"]
            for item in metrics
            if not item["passed"]
        ]
        required_actions = [
            item["required_action"]
            for item in metrics
            if item["required_action"]
        ]
        ranked_bottlenecks = sorted(
            (
                item
                for item in metrics
                if not item["passed"]
            ),
            key=lambda item: item["gap"],
        )
        dominant_bottleneck = (
            ranked_bottlenecks[-1]
            if ranked_bottlenecks
            else None
        )
        qualified = not blocked_metrics
        current_state = belief.state.value
        stage_eligible = belief.state in [
            BeliefState.VALIDATED,
            BeliefState.TRUTH_CANDIDATE,
            BeliefState.TRUTH_COMMITTED,
        ]
        eligible = qualified and stage_eligible
        metrics_passed = len(metrics) - len(blocked_metrics)
        progress_ratio = round(
            metrics_passed / max(len(metrics), 1),
            4,
        )
        eligibility_reason = (
            "truth_candidate_ready"
            if eligible
            else "truth_candidate_contextual_boundary_required"
            if (
                "contradiction_score" not in blocked_metrics
                and causal_boundary_alignment[
                    "contradiction_adjustment"
                ] > 0
            )
            else "truth_candidate_contradiction_review_required"
            if (
                blocked_metrics == ["contradiction_score"]
                and contradiction_review[
                    "within_soft_review_zone"
                ]
            )
            else "truth_candidate_metric_gaps"
            if blocked_metrics
            else "validated_stage_required"
        )
        candidate_state = (
            "REJECTED"
            if belief.state == BeliefState.REJECTED
            else "READY_FOR_TRUTH_COMMIT_REVIEW"
            if belief.state in [
                BeliefState.TRUTH_CANDIDATE,
                BeliefState.TRUTH_COMMITTED,
            ]
            else "ADVANCING_TO_TRUTH_CANDIDATE"
            if belief.state == BeliefState.VALIDATED
            else "PRE_VALIDATION"
        )

        return {
            "system": "truth_candidate_engine",
            "concept": belief.concept,
            "current_state": current_state,
            "candidate_state": candidate_state,
            "validated_knowledge":
            belief.state
            in [
                BeliefState.VALIDATED,
                BeliefState.TRUTH_CANDIDATE,
                BeliefState.TRUTH_COMMITTED,
            ],
            "qualified_metrics": qualified,
            "stage_eligible_for_truth_candidate": stage_eligible,
            "metrics_eligible_for_truth_candidate": qualified,
            "eligible_for_truth_candidate": eligible,
            "eligibility_reason": eligibility_reason,
            "metric_progress": {
                "passed_count": metrics_passed,
                "required_count": len(metrics),
                "progress_ratio": progress_ratio,
            },
            "metrics": metrics,
            "blocked_metrics": blocked_metrics,
            "ranked_bottlenecks": ranked_bottlenecks,
            "dominant_bottleneck": dominant_bottleneck,
            "required_actions": required_actions,
            **contradiction_review,
            "raw_contradiction_score": raw_contradiction_score,
            "causal_boundary_alignment": causal_boundary_alignment,
            "semantic_spine_recovery":
            self._semantic_spine_recovery(context),
            "minimum_independent_tasks":
            self.MINIMUM_INDEPENDENT_TASKS,
            "automatic_truth_commit_forbidden": True,
        }


__all__ = [
    "TruthCandidateEngine",
]
