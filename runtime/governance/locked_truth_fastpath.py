from runtime.truth.current_truth_admission import CurrentTruthAdmissionGate


class LockedTruthFastPath:
    SKIPPED_MODULES = [
        "dependency_reasoning",
        "context_discovery",
        "context_hierarchy",
        "semantic_context_validation",
        "causal_validation",
        "truth_candidate_evaluation",
        "contextual_truth_validation",
        "truth_commit_review",
    ]

    def __init__(self, admission_gate=None):
        self.admission_gate = admission_gate or CurrentTruthAdmissionGate()

    def evaluate(self, concept: str, context: dict) -> dict:
        context = context if isinstance(context, dict) else {}
        truth_report = context.get("truth_commit_report")
        if not isinstance(truth_report, dict) or not truth_report:
            return self._inactive(concept, "missing_truth_commit_report")

        admission = self.admission_gate.admit_current_truth(
            truth_report,
            consumer_scope="locked_truth_fastpath",
        )
        if not admission.admitted:
            report = self._inactive(concept, admission.admission_reason)
            report["current_truth_admission"] = admission.to_dict()
            return report

        required = {
            "final_commit_state": "LOCKED_TRUTH_PRESERVED",
            "decision": "TRUTH_COMMITTED",
            "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
            "identity_runtime_ready": True,
            "contextual_truth_supported": True,
        }
        for field, expected in required.items():
            value = self._field(field, truth_report, context)
            if value != expected:
                return self._inactive(concept, f"{field}_not_{expected}")

        contradiction = self._field(
            "effective_contradiction",
            truth_report,
            context,
        )
        threshold = self._field(
            "contradiction_threshold",
            truth_report,
            context,
        )
        if contradiction is None:
            return self._inactive(concept, "missing_effective_contradiction")
        if threshold is None:
            return self._inactive(concept, "missing_contradiction_threshold")
        try:
            if float(contradiction) >= float(threshold):
                return self._inactive(
                    concept,
                    "effective_contradiction_not_below_threshold",
                )
        except (TypeError, ValueError):
            return self._inactive(concept, "invalid_contradiction_metrics")

        recovery_state = self._field("recovery_state", truth_report, context)
        remaining_cycles = self._field(
            "remaining_recovery_cycles",
            truth_report,
            context,
        )
        recovery_stable = (
            isinstance(recovery_state, str)
            and "stable" in recovery_state.lower()
        )
        cycles_complete = remaining_cycles == 0
        if not recovery_stable and not cycles_complete:
            return self._inactive(concept, "recovery_not_stable")

        if self._has_failures(
            self._field("failed_identity_governance_gates", truth_report, context)
        ):
            return self._inactive(concept, "failed_identity_governance_gates")

        if self._has_failures(self._field("failed_gates", truth_report, context)):
            return self._inactive(concept, "failed_gates")

        if (
            self._field("contradiction_review_required", truth_report, context)
            is True
        ):
            return self._inactive(concept, "contradiction_review_required")

        return {
            "system": "locked_truth_fastpath",
            "concept": concept,
            "fastpath_active": True,
            "truth_reused": True,
            "governance_revalidation_skipped": True,
            "skipped_modules": list(self.SKIPPED_MODULES),
            "reason": "locked_truth_preserved_and_identity_stable",
            "current_truth_admission": admission.to_dict(),
        }

    def _inactive(self, concept, reason):
        return {
            "system": "locked_truth_fastpath",
            "concept": concept,
            "fastpath_active": False,
            "truth_reused": False,
            "governance_revalidation_skipped": False,
            "reason": reason,
        }

    def _field(self, field, truth_report, context):
        if field in truth_report:
            return truth_report[field]
        metadata = truth_report.get("metadata")
        if isinstance(metadata, dict) and field in metadata:
            return metadata[field]
        final_commit = truth_report.get("final_commit_decision")
        if isinstance(final_commit, dict) and field in final_commit:
            return final_commit[field]
        if field in context:
            return context[field]
        return None

    def _has_failures(self, value):
        if value is None:
            return True
        if isinstance(value, (list, tuple, set, dict)):
            return len(value) > 0
        return bool(value)
