from core.epistemic_models import (
    Belief,
    BeliefState,
    EvidenceAggregate,
    EpistemicTrial,
    TrialResult,
)
from core.truth_commit_engine import TruthCommitEngine
from runtime.semantic.invariant_boundary_engine import InvariantBoundaryEngine
from runtime.semantic.semantic_boundary_engine import SemanticBoundaryEngine


def passed_trials(concept):
    return [
        EpistemicTrial(
            concept=concept,
            support_score=1.0,
            contradiction_score=0.0,
            evidence_strength=1.0,
            semantic_consistency=1.0,
            causal_alignment=1.0,
            trial_result=TrialResult.PASSED,
            evidence_count=3,
            trial_number=number,
        )
        for number in [1, 2]
    ]


def color_context():
    return {
        "semantic_context": {
            "context_name": "color_context",
            "semantically_validated": True,
            "properties": [
                {"property_name": "color_stability", "confidence": 0.96},
                {
                    "property_name": "attribute_mapping_preservation",
                    "confidence": 0.95,
                },
                {"property_name": "no_color_reassignment", "confidence": 0.96},
                {
                    "property_name": "object_identity_preservation",
                    "confidence": 0.90,
                },
            ],
            "implications": ["color_preservation_expected"],
            "confidence": 0.96,
        },
        "context_hierarchy": {
            "hierarchy_ready": True,
            "context_hierarchy_score": 0.95,
        },
        "contextual_truth": {
            "contextual_truth_supported": True,
            "contextual_truth_score": 0.94,
        },
        "contextual_truth_authority": {
            "contextual_truth_supported": True,
            "contextual_truth_authority": 0.94,
        },
        "process_dependency_memory": {
            "resolved_dependency_chain": [
                "color_preservation",
                "color_behavior",
                "color_mapping_rule",
                "no_color_reassignment",
            ],
            "dependency_confidence": 0.94,
            "dependency_chain_coverage": 1.0,
        },
        "dependency_coherence_report": {
            "dependency_coherence": 0.94,
            "hidden_contradictions": [],
            "stable_dependencies": [
                "color_behavior",
                "color_mapping_rule",
                "no_color_reassignment",
            ],
        },
        "causal_graph_alignment": {
            "alignment_score": 0.7871,
            "alignment_ready": False,
            "components": {
                "evidence_consistency": 0.95,
                "cross_task_stability": 1.0,
                "contradiction_resistance": 0.96,
                "dependency_coherence": 0.7681,
            },
            "explanation_path": ["color_observation", "color_behavior"],
        },
        "causal_validation": {
            "validation_ready": True,
            "validation_score": 0.94,
        },
        "causal_spine_alignment": {
            "alignment_ready": True,
            "compatible_with_core_truths": True,
        },
        "causal_graph_validation": {
            "validation_ready": True,
        },
        "identity_runtime_report": {
            "runtime_ready": True,
            "runtime_state": "IDENTITY_RUNTIME_STABLE",
            "identity_split": False,
            "identity_merged": False,
            "identity_runtime_continuity": 0.86,
        },
        "identity_continuity": 0.86,
        "identity_safe_truth_integration": {
            "integration_safe": True,
            "semantic_containment": {"integration_allowed": True},
            "epistemic_drift_containment": {"integration_allowed": True},
        },
    }


def test_identity_preservation_allows_color_reassignment():
    report = InvariantBoundaryEngine().evaluate(
        "object_identity_preservation",
        semantic_context={
            "properties": [
                {"property_name": "identity_continuity"},
                {"property_name": "object_persistence"},
                {"property_name": "color_reassignment_allowed"},
            ],
        },
    )

    assert "color_reassignment" in report["allowed_variations"]
    assert "color_reassignment" in report["observed_allowed_variations"]
    assert "color_reassignment" not in report["forbidden_variations"]
    assert report["identity_attribute_separated"] is True


def test_color_preservation_forbids_color_reassignment():
    report = InvariantBoundaryEngine().evaluate(
        "color_preservation",
        semantic_context={
            "properties": [
                {"property_name": "color_stability"},
                {"property_name": "no_color_reassignment"},
                {"property_name": "color_reassignment"},
            ],
        },
    )

    assert "no_color_reassignment" in report["required_invariants"]
    assert "color_reassignment" in report["forbidden_variations"]
    assert "color_reassignment" in report["observed_forbidden_variations"]


def test_semantic_boundary_uses_invariant_separation_to_reduce_overlap():
    context = color_context()
    report = SemanticBoundaryEngine().evaluate(
        "color_preservation",
        semantic_context=context["semantic_context"],
        context_hierarchy=context["context_hierarchy"],
        contextual_truth_report=context["contextual_truth"],
        runtime_context=context,
    )

    assert report["review_required"] is False
    assert report["semantic_drift_score"] <= 0.18
    assert report["invariant_overlap_score"] <= 0.20
    assert report["invariant_boundary_report"][
        "identity_attribute_separated"
    ] is True


def test_color_preservation_commit_recovers_with_invariant_boundary():
    engine = TruthCommitEngine()
    engine.truth_registry["color_preservation"] = {
        "concept": "color_preservation",
        "status": "ACTIVE",
        "reusable": True,
    }
    belief = Belief(
        concept="color_preservation",
        claim="color_preservation is stable",
        state=BeliefState.TRUTH_COMMITTED,
        confidence=0.95,
    )
    aggregate = EvidenceAggregate(
        concept="color_preservation",
        evidence_count=6,
        evidence_strength=0.94,
        contradiction_score=0.04,
        semantic_consistency=0.97,
        causal_alignment=0.96,
    )

    commit = engine.evaluate(
        belief,
        aggregate,
        passed_trials("color_preservation"),
        color_context(),
    )

    assert commit.decision == "TRUTH_COMMITTED"
    assert commit.metadata["gates"]["semantic_drift_below_limit"] is True
    assert commit.metadata["gates"]["causal_graph_alignment"] is True
    assert commit.metadata["identity_governance"][
        "identity_runtime_split"
    ] is False
    assert commit.metadata["invariant_boundary_report"][
        "invariant_overlap_score"
    ] <= 0.20
