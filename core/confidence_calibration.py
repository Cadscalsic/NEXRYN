from core.epistemic_models import clamp


class ConfidenceCalibrator:
    def calibrate(self, hypothesis, aggregate, trials):
        passed_trials = sum(trial.trial_result.value == "PASSED" for trial in trials)
        failed_trials = sum(trial.trial_result.value == "FAILED" for trial in trials)
        inconclusive_trials = sum(
            trial.trial_result.value == "INCONCLUSIVE"
            for trial in trials
        )
        trial_reliability = clamp(
            (
                passed_trials
                + inconclusive_trials * 0.50
                + 0.5
            )
            /
            max(
                passed_trials
                + inconclusive_trials * 0.50
                + failed_trials * 1.5
                + 1.0,
                1.0,
            )
        )
        evidence_coverage = clamp(aggregate.evidence_count / 3.0)

        calibrated_confidence = clamp(
            aggregate.evidence_strength * 0.30
            + (1.0 - aggregate.contradiction_score) * 0.20
            + aggregate.historical_reliability * 0.14
            + aggregate.semantic_consistency * 0.12
            + aggregate.causal_alignment * 0.12
            + trial_reliability * 0.08
            + evidence_coverage * 0.04
        )

        return {
            "system": "confidence_calibration",
            "concept": hypothesis.concept,
            "raw_confidence": hypothesis.prior_confidence,
            "calibrated_confidence": calibrated_confidence,
            "confidence_delta": clamp(
                calibrated_confidence - hypothesis.prior_confidence,
                -1.0,
                1.0,
            ),
            "historical_reliability": aggregate.historical_reliability,
            "semantic_consistency": aggregate.semantic_consistency,
            "causal_alignment": aggregate.causal_alignment,
            "contradiction_score": aggregate.contradiction_score,
            "passed_trials": passed_trials,
            "inconclusive_trials": inconclusive_trials,
            "failed_trials": failed_trials,
            "trial_reliability": trial_reliability,
            "confidence_is_not_truth": True,
        }
