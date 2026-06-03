from runtime.concept_scope_optimizer import ConceptScopeOptimizer
from runtime.matched_boundary_runner import MatchedBoundaryRunner


class BoundaryRefinementEngine:
    def __init__(self, scope_optimizer=None, matched_boundary_runner=None):
        self.scope_optimizer = scope_optimizer or ConceptScopeOptimizer()
        self.matched_boundary_runner = (
            matched_boundary_runner or MatchedBoundaryRunner()
        )
        self._reports = {}

    def evaluate(self, concept, causal_failure_analysis=None):
        causal_failure_analysis = causal_failure_analysis or {}
        concept_scope = self.scope_optimizer.optimize(
            concept,
            causal_failure_analysis.get("boundary_conditions", []),
        )
        matched_boundary = self.matched_boundary_runner.plan(
            concept,
            concept_scope,
        )
        mixed_outcomes = causal_failure_analysis.get(
            "mixed_outcomes_detected",
            False,
        )
        report = {
            "system": "boundary_refinement_engine",
            "phase": "6.96",
            "concept": concept,
            "refinement_state": (
                "MATCHED_BOUNDARY_REPLICATION_REQUIRED"
                if mixed_outcomes and matched_boundary["matched_pair_count"]
                else "AWAITING_MIXED_CAUSAL_OUTCOMES"
            ),
            "concept_scope_optimizer": concept_scope,
            "matched_boundary_runner": matched_boundary,
            "boundary_targets": concept_scope[
                "provisional_scope"
            ]["boundary_targets"],
            "matched_boundary_probes":
            matched_boundary["matched_boundary_probes"],
            "refined_scope_requires_measured_replication": True,
            "automatic_truth_promotion_forbidden": True,
        }
        self._reports[concept] = report
        return report

    def report_for(self, concept):
        return self._reports.get(concept, {})


__all__ = [
    "BoundaryRefinementEngine",
]
