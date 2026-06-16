from core.epistemic_models import (
    Belief,
    BeliefState,
    EvidenceAggregate,
    EpistemicTrial,
    TrialResult,
)
from core.truth_commit_engine import TruthCommitEngine
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


def color_semantic_context(extra_properties=None):
    properties = [
        {"property_name": "color_stability", "confidence": 0.95},
        {
            "property_name": "attribute_mapping_preservation",
            "confidence": 0.94,
        },
        {"property_name": "no_color_reassignment", "confidence": 0.96},
    ]
    properties.extend(extra_properties or [])
    return {
        "context_name": "color_context",
        "semantically_validated": True,
        "properties": properties,
        "capabilities": [
            "color_preservation_reasoning",
            "attribute_mapping",
            "contextual_color_stability",
        ],
        "constraints": [
            "requires_color_observation",
            "invalid_under_unmapped_recoloring",
        ],
        "implications": [
            "color_preservation_expected",
            "attribute_mapping_preservation_expected",
        ],
        "confidence": 0.96,
    }


def stable_commit_context(semantic_context):
    return {
        "semantic_drift": 0.77,
        "identity_continuity": 0.86,
        "identity_safe_truth_integration": {
            "integration_safe": True,
            "semantic_containment": {
                "integration_allowed": True,
            },
            "epistemic_drift_containment": {
                "integration_allowed": True,
            },
        },
        "identity_runtime_report": {
            "runtime_ready": True,
            "runtime_state": "IDENTITY_RUNTIME_STABLE",
            "identity_split": False,
            "identity_merged": False,
            "identity_runtime_continuity": 0.86,
        },
        "context_hierarchy": {
            "hierarchy_ready": True,
            "context_hierarchy_score": 0.95,
            "root_context": "color_context",
            "child_contexts": [
                "color_preservation",
                "color_stability",
                "attribute_mapping_preservation",
            ],
        },
        "semantic_context": semantic_context,
        "contextual_truth": {
            "contextual_truth_supported": True,
            "contextual_truth_score": 0.94,
        },
        "contextual_truth_authority": {
            "contextual_truth_supported": True,
            "contextual_truth_authority": 0.94,
        },
        "causal_spine_alignment": {
            "alignment_ready": True,
            "compatible_with_core_truths": True,
        },
        "causal_graph_validation": {
            "validation_ready": True,
        },
        "causal_graph_alignment": {
            "alignment_ready": True,
        },
        "causal_validation": {
            "validation_ready": True,
            "validation_score": 0.95,
        },
    }


def test_semantic_boundary_engine_preserves_color_boundary():
    report = SemanticBoundaryEngine().evaluate(
        "color_preservation",
        semantic_context=color_semantic_context(),
    )

    assert report["concept"] == "color_preservation"
    assert report["semantic_drift_score"] <= 0.18
    assert report["boundary_integrity"] >= 0.80
    assert "color_stability" in report["core_invariants"]
    assert report["forbidden_expansions"] == []
    assert report["review_required"] is False


def test_semantic_boundary_engine_flags_forbidden_color_expansion():
    report = SemanticBoundaryEngine().evaluate(
        "color_preservation",
        semantic_context=color_semantic_context([
            {"property_name": "color_expansion", "confidence": 0.90},
        ]),
    )

    assert report["review_required"] is True
    assert "color_expansion" in report["forbidden_expansions"]
    assert report["semantic_drift_score"] > 0.18


def test_color_preservation_locked_truth_returns_to_committed_under_boundary():
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
        stable_commit_context(color_semantic_context()),
    )

    gates = commit.metadata["gates"]
    boundary = commit.metadata["semantic_boundary_report"]
    identity_governance = commit.metadata["identity_governance"]

    assert commit.decision == "TRUTH_COMMITTED"
    assert commit.metadata["final_commit_decision"]["final_commit_state"] == (
        "LOCKED_TRUTH_PRESERVED"
    )
    assert commit.metadata["identity_governance_state"] == (
        "IDENTITY_GOVERNANCE_STABLE"
    )
    assert gates["semantic_drift_below_limit"] is True
    assert gates["causal_graph_alignment"] is True
    assert boundary["review_required"] is False
    assert identity_governance["identity_runtime_split"] is False
    assert identity_governance["identity_runtime_continuity"] > 0.80
