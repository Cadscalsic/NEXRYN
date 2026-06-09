from core.causal.causal_explainer import CausalExplainer
from core.causal.causal_graph import CausalGraph
from core.causal.causal_report_builder import CausalReportBuilder
from core.causal.causal_validator import CausalValidator
from core.causal.contextual_truth_mapper import ContextualTruthMapper
from core.causal.counterfactual_reasoner import CounterfactualReasoner
from core.causal.dependency_tracker import DependencyTracker
from core.causal.identity_continuity_adapter import IdentityContinuityAdapter
from core.causal.root_cause_analyzer import RootCauseAnalyzer
from core.epistemic_models import clamp


class CausalAlignmentEngine:
    """High-level engine for causal truth readiness reports."""

    def __init__(
        self,
        graph=None,
        dependency_tracker=None,
        counterfactual_reasoner=None,
        validator=None,
        explainer=None,
        root_cause_analyzer=None,
        report_builder=None,
        contextual_truth_mapper=None,
        identity_adapter=None,
    ):
        self.graph = graph or CausalGraph()
        self.dependency_tracker = dependency_tracker or DependencyTracker()
        self.counterfactual_reasoner = (
            counterfactual_reasoner or CounterfactualReasoner()
        )
        self.validator = validator or CausalValidator()
        self.explainer = explainer or CausalExplainer()
        self.root_cause_analyzer = root_cause_analyzer or RootCauseAnalyzer()
        self.report_builder = report_builder or CausalReportBuilder()
        self.contextual_truth_mapper = (
            contextual_truth_mapper or ContextualTruthMapper()
        )
        self.identity_adapter = identity_adapter or IdentityContinuityAdapter()

    def _concept_confidence(self, concept_metrics, truth_candidate_report):
        concept_metrics = concept_metrics or {}
        truth_candidate_report = truth_candidate_report or {}
        return clamp(
            concept_metrics.get(
                "confidence",
                concept_metrics.get(
                    "support_score",
                    truth_candidate_report.get(
                        "confidence",
                        truth_candidate_report.get("support_score", 0.5),
                    ),
                ),
            )
        )

    def _recommended_action(self, validation, counterfactual):
        status = validation["status"]
        if status == "VALIDATED":
            if validation["context_consistency"] < 0.75:
                return "REQUIRE_CONTEXTUAL_TRUTH"
            return "COMMIT_TRUTH"
        if status == "PARTIALLY_VALIDATED":
            if counterfactual.get("requires_counterfactual_testing"):
                return "REQUIRE_COUNTERFACTUAL_TESTING"
            return "HOLD_FOR_MORE_EVIDENCE"
        if status == "PROVISIONAL":
            return "HOLD_FOR_MORE_EVIDENCE"
        return "BLOCK_TRUTH_COMMIT"

    def evaluate(
        self,
        concept,
        concept_metrics=None,
        context_report=None,
        semantic_context_report=None,
        truth_candidate_report=None,
        contradiction_report=None,
        world_model_report=None,
        identity_governance_report=None,
        contradiction_score=0.0,
    ):
        concept_metrics = concept_metrics or {}
        context_report = context_report or {}
        semantic_context_report = semantic_context_report or {}
        truth_candidate_report = truth_candidate_report or {}
        contradiction_report = contradiction_report or {}
        world_model_report = world_model_report or {}
        identity_governance_report = identity_governance_report or {}
        contradiction_score = contradiction_report.get(
            "contradiction_score",
            contradiction_score,
        )
        confidence = self._concept_confidence(
            concept_metrics,
            truth_candidate_report,
        )

        concept_node = self.graph.ensure_concept(
            concept,
            confidence=confidence,
            metadata={"metrics": concept_metrics},
        )
        outcome_node = self.graph.ensure_outcome(concept, confidence=confidence)
        self.graph.add_edge(
            source=concept_node.node_id,
            target=outcome_node.node_id,
            relation_type="explains",
            confidence=confidence,
            evidence=[truth_candidate_report or concept_metrics],
        )

        dependencies = self.dependency_tracker.attach_dependencies(
            self.graph,
            concept,
            context_report,
        )
        dependency_report = self.dependency_tracker.report(
            concept,
            context_report,
        )
        counterfactual = self.counterfactual_reasoner.test(
            concept,
            context_report,
        )
        identity_report = self.identity_adapter.evaluate(
            identity_governance_report,
            context_report,
        )
        semantic_context_report = {
            **semantic_context_report,
            "identity_compatibility": identity_report[
                "identity_continuity"
            ],
        }
        contextual_truth = self.contextual_truth_mapper.map_truth(
            concept,
            context_report=context_report,
            dependencies=dependencies,
            counterfactual_report=counterfactual,
        )
        validation = self.validator.validate(
            concept,
            self.graph,
            dependencies=dependencies,
            contradiction_score=contradiction_score,
            semantic_context_report=semantic_context_report,
            counterfactual_report=counterfactual,
        )
        dependency_report = validation.get(
            "dependency_report",
            dependency_report,
        )
        if world_model_report:
            stability = clamp(
                world_model_report.get("causal_stability", 0.5)
            )
            validation["causal_validation_score"] = clamp(
                (
                    validation["causal_validation_score"]
                    + stability
                    + clamp(
                        1.0 - world_model_report.get(
                            "contradiction_risk",
                            0.5,
                        )
                    )
                )
                / 3.0
            )
        if identity_governance_report:
            identity_passed = all([
                identity_governance_report.get("identity_governance", True),
                identity_governance_report.get("identity_continuity", True),
                identity_governance_report.get("semantic_integrity", True),
                identity_governance_report.get("ontology_integrity", True),
            ])
            if not identity_passed:
                validation["status"] = "BLOCKED"
                validation.setdefault("failed_dependencies", []).append({
                    "concept": concept,
                    "dependency": "identity_governance",
                    "requires_review": True,
                    "supported": False,
                })
        explanation = self.explainer.explain(
            concept,
            self.graph,
            dependencies=dependencies,
            validation=validation,
        )
        root_cause = self.root_cause_analyzer.analyze(
            self.graph,
            outcome_node.node_id,
        )
        recommended_action = self._recommended_action(
            validation,
            counterfactual,
        )
        supported = (
            validation["status"] in {"VALIDATED", "PARTIALLY_VALIDATED"}
            and recommended_action != "BLOCK_TRUTH_COMMIT"
        )

        report = {
            "system": "causal_alignment_engine",
            "concept": concept,
            "causal_alignment_supported": supported,
            "causal_graph_alignment":
            validation["causal_graph_alignment"],
            "causal_validation_score":
            validation["causal_validation_score"],
            "dependency_coherence": validation["dependency_coherence"],
            "contradiction_resistance":
            validation["contradiction_resistance"],
            "context_consistency": validation["context_consistency"],
            "identity_compatibility": validation["identity_compatibility"],
            "causal_path_completeness":
            validation["causal_path_completeness"],
            "path_completeness": validation["causal_path_completeness"],
            "status": validation["status"],
            "why": explanation["why"],
            "how_we_know": explanation["how_we_know"],
            "when_valid": explanation["when_valid"],
            "when_invalid": explanation["when_invalid"],
            "root_cause": root_cause,
            "supporting_factors": explanation["supporting_dependencies"],
            "contradicting_factors": explanation["contradicting_dependencies"],
            "dependency_chain":
            self.dependency_tracker.build_dependency_chain(
                concept,
                context_report,
            ),
            "dependency_report": dependency_report,
            "contextual_truth_report": contextual_truth,
            "identity_continuity_report": identity_report,
            "causal_chain": root_cause.get("best_causal_chain", []),
            "counterfactual_result":
            counterfactual.get("counterfactual_status"),
            "explanation_path": validation["explanation_path"],
            "failed_dependencies": validation["failed_dependencies"],
            "counterfactual_report": counterfactual,
            "recommended_action": recommended_action,
        }
        report["runtime_report"] = self.report_builder.build(
            concept,
            alignment_report=report,
            root_cause_report=root_cause,
            counterfactual_report=counterfactual,
            dependency_report=dependency_report,
            contextual_truth_report=contextual_truth,
            identity_report=identity_report,
        )
        return report


__all__ = [
    "CausalAlignmentEngine",
]
