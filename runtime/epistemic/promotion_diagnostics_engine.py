class PromotionDiagnosticsEngine:
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
    ):
        return {
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
                0.10,
                aggregate.contradiction_score < 0.10,
                "contradiction_above_truth_candidate_limit",
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
