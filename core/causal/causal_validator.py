from core.epistemic_models import clamp
from core.causal.dependency_coherence_engine import DependencyCoherenceEngine


class CausalValidator:
    """Scores causal graph quality before truth commitment."""

    def __init__(self, validation_threshold=0.75):
        self.validation_threshold = clamp(validation_threshold)
        self.dependency_engine = DependencyCoherenceEngine()

    def status_for(self, score, path_complete, failed_dependencies):
        if failed_dependencies:
            return "BLOCKED"
        if score >= self.validation_threshold and path_complete:
            return "VALIDATED"
        if score >= 0.55:
            return "PARTIALLY_VALIDATED"
        if score >= 0.30:
            return "PROVISIONAL"
        return "BLOCKED"

    def validate(
        self,
        concept,
        graph,
        dependencies=None,
        contradiction_score=0.0,
        semantic_context_report=None,
        counterfactual_report=None,
    ):
        dependencies = list(dependencies or [])
        semantic_context_report = semantic_context_report or {}
        counterfactual_report = counterfactual_report or {}
        complete, path = graph.concept_path_complete(concept)

        supporting = [item for item in dependencies if item["supported"]]
        failed = [
            item
            for item in dependencies
            if item["requires_review"] and not item["supported"]
        ]

        dependency_report = self.dependency_engine.evaluate(
            dependencies,
            graph=graph,
            concept=concept,
        )
        dependency_coherence = dependency_report["dependency_coherence"]
        contradiction_resistance = clamp(1.0 - contradiction_score)
        context_consistency = clamp(
            semantic_context_report.get(
                "semantic_context_score",
                semantic_context_report.get(
                    "contextual_truth_score",
                    dependency_coherence,
                ),
            )
        )
        identity_compatibility = clamp(
            semantic_context_report.get(
                "identity_compatibility",
                1.0,
            )
        )
        causal_path_completeness = 1.0 if complete else 0.0
        counterfactual_robustness = clamp(
            counterfactual_report.get("counterfactual_robustness", 0.5)
        )
        causal_graph_alignment = clamp(
            (
                dependency_coherence
                + contradiction_resistance
                + context_consistency
                + identity_compatibility
                + causal_path_completeness
            )
            / 5.0
        )
        causal_validation_score = clamp(
            (
                causal_graph_alignment
                + dependency_coherence
                + contradiction_resistance
                + counterfactual_robustness
            )
            / 4.0
        )
        status = self.status_for(
            causal_validation_score,
            complete,
            failed,
        )

        return {
            "system": "causal_validator",
            "concept": concept,
            "causal_graph_alignment": causal_graph_alignment,
            "causal_validation_score": causal_validation_score,
            "dependency_coherence": dependency_coherence,
            "dependency_report": dependency_report,
            "contradiction_resistance": contradiction_resistance,
            "context_consistency": context_consistency,
            "identity_compatibility": identity_compatibility,
            "causal_path_completeness": causal_path_completeness,
            "status": status,
            "truth_governance_action": (
                "ALLOW_TRUTH_REVIEW"
                if (
                    dependency_coherence >= 0.80
                    and complete
                    and status in {"VALIDATED", "PARTIALLY_VALIDATED"}
                )
                else "HOLD_FOR_CAUSAL_REVIEW"
            ),
            "failed_dependencies": failed,
            "explanation_path": path,
            "causal_path_complete": complete,
        }


__all__ = [
    "CausalValidator",
]
