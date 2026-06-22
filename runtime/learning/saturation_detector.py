class LearningSaturationDetector:

    LEARNING_ACTIVE = "LEARNING_ACTIVE"
    LEARNING_REVIEW = "LEARNING_REVIEW"
    LEARNING_SATURATED = "LEARNING_SATURATED"
    CONCEPT_FROZEN = "CONCEPT_FROZEN"

    def __init__(self, minimum_recovery_streak=2):

        self.minimum_recovery_streak = int(minimum_recovery_streak)

    def evaluate(self, concept_name, runtime_context):

        evidence_saturated = (
            runtime_context.get("evidence_saturated") is True
        )
        dependency_chain_coverage = float(
            runtime_context.get("dependency_chain_coverage", 0.0) or 0.0
        )
        contradiction_gap = float(
            runtime_context.get("contradiction_gap", 0.0) or 0.0
        )
        transfer_reliability = float(
            runtime_context.get("transfer_reliability", 0.0) or 0.0
        )
        recovery_streak = int(
            runtime_context.get(
                "recovery_streak",
                runtime_context.get("truth_recovery_streak", 0),
            )
            or 0
        )
        validation_stability = runtime_context.get(
            "validation_stability",
            "STABLE" if contradiction_gap == 0.0 else "REVIEW",
        )
        context_stability = runtime_context.get(
            "context_stability",
            "STABLE"
            if runtime_context.get("contextual_truth_supported") is True
            else "REVIEW",
        )

        saturated = (
            evidence_saturated
            and dependency_chain_coverage >= 0.95
            and contradiction_gap == 0.0
            and transfer_reliability >= 0.85
            and recovery_streak >= self.minimum_recovery_streak
        )

        learning_state = (
            self.LEARNING_SATURATED
            if saturated
            else self.LEARNING_REVIEW
            if evidence_saturated
            else self.LEARNING_ACTIVE
        )
        recommended_next_step = (
            "freeze_concept"
            if saturated
            else runtime_context.get(
                "recommended_next_step",
                "continue_adaptive_training",
            )
        )

        report = {
            "concept_name": str(concept_name),
            "evidence_saturated": evidence_saturated,
            "dependency_chain_coverage":
            round(dependency_chain_coverage, 4),
            "contradiction_gap": round(contradiction_gap, 4),
            "validation_stability": validation_stability,
            "truth_recovery_streak": recovery_streak,
            "context_stability": context_stability,
            "transfer_reliability": round(transfer_reliability, 4),
            "recovery_streak": recovery_streak,
            "learning_state": learning_state,
            "recommended_next_step": recommended_next_step,
            "enable_adaptive_training": not saturated,
            "enable_context_reconstruction": not saturated,
            "enable_truth_rehearsal": not saturated,
            "continue_integrity_monitoring": saturated,
            "continue_anomaly_detection": saturated,
            "continue_cache_verification": saturated,
        }

        if saturated:
            report["freeze_state"] = self.CONCEPT_FROZEN

        return report


saturation_detector = LearningSaturationDetector()


__all__ = [
    "LearningSaturationDetector",
    "saturation_detector",
]
