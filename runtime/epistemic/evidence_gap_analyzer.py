class EvidenceGapAnalyzer:
    def __init__(
        self,
        required_success_examples=4,
        required_counterexamples=2,
        target_independent_tasks=5,
    ):
        self.required_success_examples = max(
            int(required_success_examples),
            1,
        )
        self.required_counterexamples = max(
            int(required_counterexamples),
            1,
        )
        self.target_independent_tasks = max(
            int(target_independent_tasks),
            1,
        )
        self._reports = {}

    def _metric_gap(self, truth_candidate, metric):
        return next(
            (
                item.get("gap", 0.0)
                for item in truth_candidate.get("metrics", [])
                if item.get("metric") == metric
            ),
            0.0,
        )

    def evaluate(
        self,
        concept,
        knowledge_generalization=None,
        causal_failure_analysis=None,
        truth_candidate=None,
    ):
        generalization = knowledge_generalization or {}
        causal_failure = causal_failure_analysis or {}
        truth_candidate = truth_candidate or {}
        store = causal_failure.get("counterexample_store", {})
        success_count = store.get("supported_observation_count", 0)
        counterexample_count = store.get("counterexample_count", 0)
        used_task_count = generalization.get("used_task_count", 0)
        missing_successes = max(
            self.required_success_examples - success_count,
            0,
        )
        missing_counterexamples = max(
            self.required_counterexamples - counterexample_count,
            0,
        )
        missing_tasks = max(
            self.target_independent_tasks - used_task_count,
            0,
        )
        evidence_strength_gap = self._metric_gap(
            truth_candidate,
            "evidence_strength",
        )
        confidence_gap = self._metric_gap(truth_candidate, "confidence")

        missing_regions = []
        if missing_successes:
            missing_regions.append({
                "region": "supported_region",
                "missing_examples": missing_successes,
                "acquisition_strategy": "discover_supported_region",
            })
        if missing_counterexamples:
            missing_regions.append({
                "region": "counterexample_region",
                "missing_examples": missing_counterexamples,
                "acquisition_strategy": "probe_counterexample_region",
            })
        if missing_tasks:
            missing_regions.append({
                "region": "independent_task_coverage",
                "missing_examples": missing_tasks,
                "acquisition_strategy":
                "independent_cross_task_execution_validation",
            })
        if causal_failure.get("mixed_outcomes_detected"):
            missing_regions.append({
                "region": "concept_boundary",
                "missing_examples": max(missing_tasks, 1),
                "acquisition_strategy": "matched_boundary_replication",
            })

        acquisition_required = bool(used_task_count and missing_regions)
        report = {
            "system": "evidence_gap_analyzer",
            "phase": "6.94",
            "concept": concept,
            "analysis_state": (
                "ACTIVE_KNOWLEDGE_ACQUISITION_REQUIRED"
                if acquisition_required
                else "AWAITING_INITIAL_EXECUTION_OBSERVATION"
                if not used_task_count
                else "EVIDENCE_COVERAGE_SUFFICIENT"
            ),
            "required_success_examples": self.required_success_examples,
            "observed_success_examples": success_count,
            "missing_success_examples": missing_successes,
            "required_counterexamples": self.required_counterexamples,
            "observed_counterexamples": counterexample_count,
            "missing_counterexamples": missing_counterexamples,
            "target_independent_tasks": self.target_independent_tasks,
            "used_task_count": used_task_count,
            "remaining_independent_tasks": missing_tasks,
            "evidence_strength_gap": evidence_strength_gap,
            "confidence_gap": confidence_gap,
            "missing_regions": missing_regions,
            "acquisition_required": acquisition_required,
            "priority": (
                "high"
                if acquisition_required and not success_count
                else "medium"
                if acquisition_required
                else "low"
            ),
            "knowledge_acquisition_is_evidence_not_truth": True,
        }
        self._reports[concept] = report
        return report

    def report_for(self, concept):
        return self._reports.get(concept, {})


__all__ = [
    "EvidenceGapAnalyzer",
]
