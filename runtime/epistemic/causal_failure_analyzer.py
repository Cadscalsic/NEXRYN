from runtime.epistemic.causal_boundary_mapper import CausalBoundaryMapper
from runtime.epistemic.causal_counterexample_store import (
    CausalCounterexampleStore,
)


class CausalFailureAnalyzer:
    def __init__(self, ledger, counterexample_store=None, boundary_mapper=None):
        self.counterexample_store = (
            counterexample_store or CausalCounterexampleStore(ledger)
        )
        self.boundary_mapper = boundary_mapper or CausalBoundaryMapper()
        self._reports = {}

    def evaluate(self, concept):
        observations = self.counterexample_store.report_for(concept)
        boundary_map = self.boundary_mapper.map(
            concept,
            observations["supported_observations"],
            observations["counterexamples"],
        )
        mixed_outcomes = bool(
            observations["supported_observation_count"]
            and observations["counterexample_count"]
        )
        report = {
            "system": "causal_failure_analyzer",
            "phase": "6.93",
            "concept": concept,
            "analysis_state": (
                "COUNTEREXAMPLE_BOUNDARY_ANALYSIS_REQUIRED"
                if mixed_outcomes
                else "CAUSAL_FAILURE_REGION_OBSERVED"
                if observations["counterexample_count"]
                else "SUPPORTED_CAUSAL_REGION_OBSERVED"
                if observations["supported_observation_count"]
                else "AWAITING_CROSS_TASK_CAUSAL_OBSERVATIONS"
            ),
            "mixed_outcomes_detected": mixed_outcomes,
            "counterexample_store": observations,
            "concept_boundary": boundary_map,
            "holds_when": boundary_map["holds_when"],
            "fails_when": boundary_map["fails_when"],
            "boundary_conditions": boundary_map["boundary_conditions"],
            "required_actions": (
                [
                    "isolate_counterexample_conditions",
                    "run_matched_boundary_replications",
                    "refine_concept_scope",
                ]
                if mixed_outcomes
                else []
            ),
            "boundary_explanation_is_not_automatic_truth_promotion": True,
        }
        self._reports[concept] = report
        return report

    def report_for(self, concept):
        return self._reports.get(concept, {})


__all__ = [
    "CausalFailureAnalyzer",
]
