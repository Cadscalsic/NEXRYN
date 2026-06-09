from core.causal import CausalAlignmentEngine, CausalGraph, CausalValidator


def test_causal_alignment_scoring_and_contextual_action():
    engine = CausalAlignmentEngine()

    report = engine.evaluate(
        "color_preservation",
        concept_metrics={"confidence": 0.95},
        context_report={"color_behavior": "unchanged"},
        semantic_context_report={
            "semantic_context_score": 0.5,
            "identity_compatibility": 1.0,
        },
        truth_candidate_report={"support_score": 0.95},
        contradiction_score=0.0,
    )

    assert report["causal_alignment_supported"] is True
    assert report["causal_graph_alignment"] >= 0.8
    assert report["causal_validation_score"] >= 0.8
    assert report["dependency_coherence"] == 1.0
    assert report["recommended_action"] == "REQUIRE_CONTEXTUAL_TRUTH"
    assert report["when_valid"] == ["color_behavior is unchanged"]


def test_blocked_truth_when_causal_path_is_incomplete():
    graph = CausalGraph()
    graph.ensure_concept("shape_preservation", confidence=0.9)
    validator = CausalValidator()

    report = validator.validate(
        "shape_preservation",
        graph,
        dependencies=[{
            "concept": "shape_preservation",
            "context_key": "transformation_family",
            "context_value": "shape_transform",
            "supported": False,
            "requires_review": True,
            "relation": "context_requires",
            "confidence": 1.0,
        }],
        contradiction_score=0.0,
        semantic_context_report={"identity_compatibility": 1.0},
        counterfactual_report={"counterfactual_robustness": 0.5},
    )

    assert report["causal_path_complete"] is False
    assert report["status"] == "BLOCKED"
    assert report["failed_dependencies"]


def test_context_dependent_truth_blocks_color_reassignment():
    engine = CausalAlignmentEngine()

    report = engine.evaluate(
        "color_preservation",
        concept_metrics={"confidence": 0.95},
        context_report={"color_behavior": "color_reassigned"},
        semantic_context_report={
            "semantic_context_score": 0.5,
            "identity_compatibility": 1.0,
        },
        truth_candidate_report={"support_score": 0.95},
        contradiction_score=0.0,
    )

    assert report["status"] == "BLOCKED"
    assert report["causal_alignment_supported"] is False
    assert report["recommended_action"] == "BLOCK_TRUTH_COMMIT"
    assert "color_behavior requires review under color_reassigned" in (
        report["when_invalid"]
    )


def test_phase_five_alignment_report_reaches_success_thresholds():
    engine = CausalAlignmentEngine()

    report = engine.evaluate(
        "shape_preservation",
        concept_metrics={"confidence": 0.98},
        context_report={
            "transformation_family": "duplication",
            "identity_behavior": "identity_preserved",
        },
        semantic_context_report={"semantic_context_score": 1.0},
        truth_candidate_report={"support_score": 0.98},
        contradiction_report={"contradiction_score": 0.0},
        world_model_report={
            "causal_stability": 0.95,
            "contradiction_risk": 0.0,
            "context_transfer_reliability": 0.95,
        },
        identity_governance_report={
            "identity_governance": True,
            "identity_continuity": 0.95,
            "semantic_integrity": True,
            "ontology_integrity": True,
        },
    )

    assert report["dependency_coherence"] > 0.8
    assert report["causal_graph_alignment"] > 0.85
    assert report["causal_validation_score"] > 0.85
    assert report["counterfactual_report"]["causal_resilience"] > 0.8
    assert report["contextual_truth_report"][
        "context_transfer_reliability"
    ] > 0.85
    assert "DEPENDENCY REPORT" in report["runtime_report"]["reports"]


def test_alignment_blocks_identity_continuity_failure():
    engine = CausalAlignmentEngine()

    report = engine.evaluate(
        "identity_preservation",
        concept_metrics={"confidence": 0.95},
        context_report={"identity_behavior": "identity_preserved"},
        semantic_context_report={"semantic_context_score": 1.0},
        truth_candidate_report={"support_score": 0.95},
        identity_governance_report={
            "identity_governance": False,
            "identity_continuity": 0.2,
        },
    )

    assert report["status"] == "BLOCKED"
    assert report["recommended_action"] == "BLOCK_TRUTH_COMMIT"
    assert report["identity_continuity_report"]["identity_continuity"] == 0.2
