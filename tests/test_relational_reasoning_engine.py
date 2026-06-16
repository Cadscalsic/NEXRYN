from core.epistemic_models import (
    Belief,
    BeliefState,
    EvidenceAggregate,
    EpistemicTrial,
    TrialResult,
)
from core.truth_commit_engine import TruthCommitEngine
from runtime.epistemic.truth_candidate_engine import TruthCandidateEngine
from runtime.relational import RelationalReasoningEngine


def symmetric_scene_graph():
    return {
        "system": "scene_graph_engine",
        "width": 5,
        "height": 3,
        "nodes": {
            "left": {
                "shape_signature": "single_cell",
                "size": 1,
                "center": {"x": 1, "y": 1},
            },
            "right": {
                "shape_signature": "single_cell",
                "size": 1,
                "center": {"x": 3, "y": 1},
            },
        },
        "edges": [],
        "summary": {
            "object_count": 2,
        },
    }


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


def symmetry_context():
    process_memory = {
        "resolved_dependency_chain": [
            "object_observation",
            "symmetry_relation",
            "symmetry_axis",
            "object_pair_mapping",
            "relation_consistency",
            "symmetry_reasoning",
        ],
        "dependency_confidence": 0.94,
        "dependency_chain_coverage": 1.0,
        "dependency_chain_depth": 6,
        "missing_dependencies": [],
    }
    return {
        "scene_graph_comparison": {
            "input_scene_graph": symmetric_scene_graph(),
            "summary": {
                "input_object_count": 2,
                "output_object_count": 2,
            },
        },
        "semantic_context": {
            "context_name": "symmetry_reasoning_context",
            "semantically_validated": True,
            "properties": [
                {"property_name": "symmetry_relation", "confidence": 0.95},
                {"property_name": "symmetry_axis", "confidence": 0.95},
                {"property_name": "object_pair_mapping", "confidence": 0.95},
                {"property_name": "relation_consistency", "confidence": 0.95},
                {"property_name": "relational_symmetry", "confidence": 0.95},
            ],
            "confidence": 0.95,
        },
        "context_hierarchy": {
            "hierarchy_ready": True,
            "context_hierarchy_score": 0.94,
        },
        "contextual_truth": {
            "contextual_truth_supported": True,
            "contextual_truth_score": 0.94,
        },
        "contextual_truth_authority": {
            "contextual_truth_supported": True,
            "contextual_truth_authority": 0.94,
        },
        "causal_graph_alignment": {
            "alignment_score": 0.7947,
            "alignment_ready": False,
            "components": {
                "evidence_consistency": 0.95,
                "cross_task_stability": 0.95,
                "contradiction_resistance": 0.94,
                "dependency_coherence": 0.91,
            },
        },
        "causal_validation": {
            "validation_ready": True,
            "validation_score": 0.91,
        },
        "causal_spine_alignment": {
            "alignment_ready": True,
            "compatible_with_core_truths": True,
        },
        "causal_graph_validation": {
            "validation_ready": True,
        },
        "process_dependency_memory": process_memory,
        "dependency_chain_alignment": {
            "alignment_ready": True,
            "alignment_confidence": 0.93,
        },
        "identity_continuity": 0.86,
        "identity_runtime_report": {
            "runtime_ready": True,
            "runtime_state": "IDENTITY_RUNTIME_STABLE",
            "identity_split": False,
            "identity_merged": False,
            "identity_runtime_continuity": 0.86,
        },
        "identity_safe_truth_integration": {
            "integration_safe": True,
            "semantic_containment": {"integration_allowed": True},
            "epistemic_drift_containment": {"integration_allowed": True},
        },
    }


def test_relational_reasoning_builds_symmetry_relation_graph():
    report = RelationalReasoningEngine().evaluate(
        "symmetry_reasoning",
        scene_graph_report={"input_scene_graph": symmetric_scene_graph()},
    )

    assert report["concept_type"] == "RELATIONAL"
    assert report["symmetry_axis"] == "vertical"
    assert report["symmetry_relations"]
    assert report["relation_consistency"] > 0.82
    assert report["relation_ready"] is True


def test_truth_candidate_uses_relational_alignment_for_symmetry_reasoning():
    belief = Belief(
        concept="symmetry_reasoning",
        claim="symmetry can be a relation",
        state=BeliefState.VALIDATED,
        confidence=0.91,
    )
    aggregate = EvidenceAggregate(
        concept="symmetry_reasoning",
        evidence_strength=0.91,
        contradiction_score=0.1526,
        semantic_consistency=0.94,
        causal_alignment=0.79,
    )

    report = TruthCandidateEngine().evaluate(
        belief,
        aggregate,
        symmetry_context(),
    )

    assert report["relational_reasoning_report"]["concept_type"] == "RELATIONAL"
    assert report["relational_reasoning_report"]["relation_ready"] is True
    assert report["causal_graph_alignment"]["alignment_score"] > 0.82
    assert "causal_graph_alignment" not in report["blocked_metrics"]


def test_truth_commit_consumes_relational_symmetry_without_forcing_truth():
    engine = TruthCommitEngine()
    engine.truth_registry["symmetry_reasoning"] = {
        "concept": "symmetry_reasoning",
        "status": "ACTIVE",
        "reusable": True,
    }
    belief = Belief(
        concept="symmetry_reasoning",
        claim="symmetry can be a relation",
        state=BeliefState.TRUTH_COMMITTED,
        confidence=0.95,
    )
    aggregate = EvidenceAggregate(
        concept="symmetry_reasoning",
        evidence_count=6,
        evidence_strength=0.94,
        contradiction_score=0.04,
        semantic_consistency=0.96,
        causal_alignment=0.90,
    )

    commit = engine.evaluate(
        belief,
        aggregate,
        passed_trials("symmetry_reasoning"),
        symmetry_context(),
    )

    gates = commit.metadata["gates"]
    assert commit.decision == "TRUTH_COMMITTED"
    assert gates["semantic_drift_below_limit"] is True
    assert gates["causal_graph_alignment"] is True
    assert commit.metadata["relational_reasoning_report"][
        "relation_consistency"
    ] > 0.82
