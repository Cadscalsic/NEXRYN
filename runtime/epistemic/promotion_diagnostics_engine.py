from core.knowledge.contradiction_review_policy import (
    SOFT_REVIEW_ZONE,
    classify_contradiction_review,
)


class PromotionDiagnosticsEngine:
    TRUTH_CANDIDATE_CONTRADICTION_LIMIT = 0.10
    TRUTH_CANDIDATE_CONTRADICTION_REVIEW_ZONE = SOFT_REVIEW_ZONE

    def _diagnostic(
        self,
        concept,
        gate_name,
        source_metric,
        current_value,
        comparator,
        required,
        passed,
        failure_reason,
        metadata=None,
    ):
        report = {
            "concept": concept,
            "gate_name": gate_name,
            "gate_threshold": {
                "comparator": comparator,
                "required": required,
            },
            "source_metric": source_metric,
            "current_value": current_value,
            "passed": passed,
            "failed": not passed,
            "status": "PASSED" if passed else "FAILED",
            "failure_reason": None if passed else failure_reason,
        }
        if metadata:
            report.update(metadata)
        return report

    def evaluate(self, aggregate, trials, calibrated_confidence):
        total_trials = len(trials)
        passed_trials = sum(
            trial.trial_result.value == "PASSED"
            for trial in trials
        )
        failed_trials = sum(
            trial.trial_result.value == "FAILED"
            for trial in trials
        )
        inconclusive_trials = total_trials - passed_trials - failed_trials
        concept = aggregate.concept
        contradiction_review = classify_contradiction_review(
            aggregate.contradiction_score,
            threshold=self.TRUTH_CANDIDATE_CONTRADICTION_LIMIT,
            soft_review_zone=(
                self.TRUTH_CANDIDATE_CONTRADICTION_REVIEW_ZONE
            ),
        )
        contradiction_passes_promotion = (
            aggregate.contradiction_score
            < self.TRUTH_CANDIDATE_CONTRADICTION_LIMIT
            or contradiction_review["within_soft_review_zone"]
        )

        diagnostics = [
            self._diagnostic(
                concept,
                "has_evidence",
                "evidence_count",
                aggregate.evidence_count,
                ">",
                0,
                aggregate.evidence_count > 0,
                "no_evidence_collected",
            ),
            self._diagnostic(
                concept,
                "contradiction_below_rejection",
                "contradiction_score",
                aggregate.contradiction_score,
                "<",
                0.55,
                aggregate.contradiction_score < 0.55,
                "contradiction_reaches_rejection_threshold",
            ),
            self._diagnostic(
                concept,
                "supported_trial",
                "passed_trials",
                passed_trials,
                ">=",
                1,
                passed_trials >= 1,
                "insufficient_passed_trials",
            ),
            self._diagnostic(
                concept,
                "supported_confidence",
                "calibrated_confidence",
                calibrated_confidence,
                ">=",
                0.64,
                calibrated_confidence >= 0.64,
                "confidence_below_supported_threshold",
            ),
            self._diagnostic(
                concept,
                "validated_trials",
                "passed_trials",
                passed_trials,
                ">=",
                2,
                passed_trials >= 2,
                "insufficient_passed_trials",
            ),
            self._diagnostic(
                concept,
                "validated_confidence",
                "calibrated_confidence",
                calibrated_confidence,
                ">=",
                0.78,
                calibrated_confidence >= 0.78,
                "confidence_below_validated_threshold",
            ),
            self._diagnostic(
                concept,
                "validated_consistency",
                "semantic_consistency",
                aggregate.semantic_consistency,
                ">=",
                0.72,
                aggregate.semantic_consistency >= 0.72,
                "semantic_consistency_below_validated_threshold",
            ),
            self._diagnostic(
                concept,
                "truth_candidate_strength",
                "evidence_strength",
                aggregate.evidence_strength,
                ">=",
                0.80,
                aggregate.evidence_strength >= 0.80,
                "evidence_strength_below_truth_candidate_threshold",
            ),
            self._diagnostic(
                concept,
                "truth_candidate_confidence",
                "calibrated_confidence",
                calibrated_confidence,
                ">=",
                0.85,
                calibrated_confidence >= 0.85,
                "confidence_below_truth_candidate_threshold",
            ),
            self._diagnostic(
                concept,
                "truth_candidate_contradiction",
                "contradiction_score",
                aggregate.contradiction_score,
                "<",
                self.TRUTH_CANDIDATE_CONTRADICTION_LIMIT,
                contradiction_passes_promotion,
                "contradiction_above_truth_candidate_limit",
                {
                    **contradiction_review,
                    "soft_review_permits_truth_candidate_promotion":
                    contradiction_review["within_soft_review_zone"],
                    "truth_commit_review_still_required":
                    contradiction_review["contradiction_review_required"],
                },
            ),
            self._diagnostic(
                concept,
                "truth_candidate_causality",
                "causal_alignment",
                aggregate.causal_alignment,
                ">=",
                0.80,
                aggregate.causal_alignment >= 0.80,
                "causal_alignment_below_truth_candidate_threshold",
            ),
        ]

        return {
            "system": "promotion_diagnostics_engine",
            "concept": concept,
            "trial_counts": {
                "total": total_trials,
                "passed": passed_trials,
                "failed": failed_trials,
                "inconclusive": inconclusive_trials,
            },
            "gates": diagnostics,
        }


__all__ = [
    "PromotionDiagnosticsEngine",
]
