from core.context import ContextualTruthAuthorityEngine


def shape_inputs():
    return {
        "concept": "shape_preservation",
        "truth_candidate_report": {
            "contextual_truth_score": 0.6874,
            "effective_contradiction": 0.1077,
            "contradiction_threshold": 0.1,
            "contradiction_review_required": True,
            "contradiction_review_severity": "LOW_RISK_REVIEW",
        },
        "context_consistency_report": {
            "context_signature": "duplication",
            "context_consistency": 0.765,
        },
        "contextual_truth_report": {
            "context_confidence": 0.8228,
            "transfer_reliability": 0.4444,
            "status": "CONTEXT_REVIEW_REQUIRED",
        },
        "semantic_context_report": {
            "confidence": 0.9,
            "status": "SEMANTICALLY_VALIDATED",
        },
        "context_hierarchy_report": {
            "score": 0.94,
            "hierarchy_ready": True,
        },
        "causal_validation_report": {
            "causal_validation_score": 0.8048,
            "causal_graph_alignment": 0.8325,
            "dependency_coherence": 0.6542,
            "contradiction_resistance": 0.8696,
            "identity_compatibility": 1.0,
        },
        "identity_report": {
            "identity_governance_state":
            "IDENTITY_GOVERNANCE_REVIEW_REQUIRED",
            "identity_state": "HOLD_FOR_IDENTITY_SAFETY",
            "failed_identity_governance_gates": [
                "semantic_drift_below_limit",
                "identity_continuity_above_limit",
            ],
        },
    }


def test_input_normalization_uses_aliases_and_defaults():
    engine = ContextualTruthAuthorityEngine()

    data = engine.normalize_inputs(
        "shape_preservation",
        truth_candidate_report={"contextual_truth_score": 0.7},
        context_hierarchy_report={"score": 0.9},
        causal_validation_report={
            "validation_score": 0.8,
            "causal_graph_alignment": {"alignment_score": 0.82},
        },
    )

    assert data["concept"] == "shape_preservation"
    assert data["contextual_truth_score"] == 0.7
    assert data["context_hierarchy_score"] == 0.9
    assert data["causal_validation_score"] == 0.8
    assert data["causal_graph_alignment"] == 0.82
    assert data["context_consistency"] == 0.5


def test_context_authority_scoring_combines_context_signals():
    engine = ContextualTruthAuthorityEngine()
    data = engine.normalize_inputs(**shape_inputs())

    score = engine.compute_context_authority_score(data)

    assert 0.70 <= score <= 0.80


def test_causal_support_scoring_uses_causal_components():
    engine = ContextualTruthAuthorityEngine()
    data = engine.normalize_inputs(**shape_inputs())

    score = engine.compute_causal_support_score(data)

    assert 0.75 <= score <= 0.85


def test_identity_safety_scoring_penalizes_review_state():
    engine = ContextualTruthAuthorityEngine()
    data = engine.normalize_inputs(**shape_inputs())

    score = engine.compute_identity_safety_score(data)

    assert 0.40 <= score <= 0.65


def test_contradiction_penalty_calculation():
    engine = ContextualTruthAuthorityEngine()
    data = engine.normalize_inputs(**shape_inputs())

    penalty = engine.compute_contradiction_penalty(data)

    assert 0.50 <= penalty <= 0.75


def test_final_authority_classification():
    engine = ContextualTruthAuthorityEngine()

    assert engine.classify_authority(
        0.86,
        {},
    ) == "AUTHORITATIVE_CONTEXTUAL_TRUTH"
    assert engine.classify_authority(
        0.76,
        {},
    ) == "SUPPORTED_CONTEXTUAL_TRUTH"
    assert engine.classify_authority(
        0.61,
        {},
    ) == "PROVISIONAL_CONTEXTUAL_TRUTH"
    assert engine.classify_authority(
        0.46,
        {},
    ) == "CONTEXT_REVIEW_REQUIRED"
    assert engine.classify_authority(
        0.30,
        {},
    ) == "BLOCKED_CONTEXTUAL_TRUTH"


def test_truth_governance_action_recommendation():
    engine = ContextualTruthAuthorityEngine()
    data = {
        "context_consistency": 0.8,
        "causal_support_score": 0.8,
        "identity_safety_score": 0.9,
        "contradiction_penalty": 0.1,
        "failed_identity_governance_gates": [],
        "identity_failed_checks": [],
    }

    assert engine.recommend_truth_governance_action(
        "SUPPORTED_CONTEXTUAL_TRUTH",
        data,
    ) == "COMMIT_CONTEXTUAL_TRUTH"
    assert engine.recommend_truth_governance_action(
        "PROVISIONAL_CONTEXTUAL_TRUTH",
        data,
    ) == "HOLD_FOR_CONTEXT_REVIEW"


def test_missing_input_behavior_is_runtime_safe():
    engine = ContextualTruthAuthorityEngine()

    report = engine.analyze("unknown_concept")

    assert report["system"] == "contextual_truth_authority_engine"
    assert 0.0 <= report["contextual_truth_authority"] <= 1.0
    assert report["truth_governance_action"] in {
        "COMMIT_CONTEXTUAL_TRUTH",
        "HOLD_FOR_CONTEXT_REVIEW",
        "REQUIRE_MORE_CONTEXT_EVIDENCE",
        "REQUIRE_CAUSAL_REVIEW",
        "REQUIRE_IDENTITY_REVIEW",
        "BLOCK_TRUTH_COMMIT",
    }


def test_strong_contextual_truth_supports_commit():
    engine = ContextualTruthAuthorityEngine()

    report = engine.analyze(
        "shape_preservation",
        truth_candidate_report={
            "contextual_truth_score": 0.92,
            "effective_contradiction": 0.01,
            "contradiction_threshold": 0.1,
        },
        context_consistency_report={"context_consistency": 0.91},
        contextual_truth_report={
            "context_confidence": 0.94,
            "transfer_reliability": 0.90,
        },
        semantic_context_report={"confidence": 0.94},
        context_hierarchy_report={"score": 0.93},
        causal_validation_report={
            "causal_validation_score": 0.92,
            "causal_graph_alignment": 0.91,
            "dependency_coherence": 0.88,
            "contradiction_resistance": 0.99,
            "identity_compatibility": 0.96,
        },
        identity_report={
            "identity_governance_state": "IDENTITY_GOVERNANCE_STABLE",
            "identity_state": "IDENTITY_REINFORCING_TRUTH",
        },
    )

    assert report["contextual_truth_supported"] is True
    assert report["authority_status"] in {
        "AUTHORITATIVE_CONTEXTUAL_TRUTH",
        "SUPPORTED_CONTEXTUAL_TRUTH",
    }
    assert report["truth_governance_action"] in {
        "COMMIT_TRUTH",
        "COMMIT_CONTEXTUAL_TRUTH",
    }


def test_weak_contextual_truth_requires_review():
    engine = ContextualTruthAuthorityEngine()

    report = engine.analyze(
        "shape_preservation",
        truth_candidate_report={"contextual_truth_score": 0.45},
        context_consistency_report={"context_consistency": 0.50},
        contextual_truth_report={
            "context_confidence": 0.45,
            "transfer_reliability": 0.40,
        },
        causal_validation_report={"causal_validation_score": 0.65},
    )

    assert report["contextual_truth_supported"] is False
    assert report["authority_status"] in {
        "PROVISIONAL_CONTEXTUAL_TRUTH",
        "CONTEXT_REVIEW_REQUIRED",
        "BLOCKED_CONTEXTUAL_TRUTH",
    }


def test_blocked_truth_behavior():
    engine = ContextualTruthAuthorityEngine()

    report = engine.analyze(
        "shape_preservation",
        truth_candidate_report={
            "contextual_truth_score": 0.20,
            "effective_contradiction": 0.30,
            "contradiction_threshold": 0.1,
            "contradiction_review_required": True,
            "contradiction_review_severity": "HIGH_RISK_REVIEW",
        },
        context_consistency_report={"context_consistency": 0.20},
        contextual_truth_report={
            "context_confidence": 0.30,
            "transfer_reliability": 0.20,
        },
        causal_validation_report={
            "causal_validation_score": 0.20,
            "causal_graph_alignment": 0.25,
            "dependency_coherence": 0.20,
            "contradiction_resistance": 0.20,
        },
    )

    assert report["authority_status"] == "BLOCKED_CONTEXTUAL_TRUTH"
    assert report["truth_governance_action"] in {
        "REQUIRE_CAUSAL_REVIEW",
        "BLOCK_TRUTH_COMMIT",
    }


def test_shape_preservation_with_improved_context_consistency():
    engine = ContextualTruthAuthorityEngine()

    report = engine.analyze(**shape_inputs())

    assert report["context_authority_score"] >= 0.70
    assert report["causal_support_score"] >= 0.75
    assert report["authority_status"] == "PROVISIONAL_CONTEXTUAL_TRUTH"
    assert report["truth_governance_action"] in {
        "HOLD_FOR_CONTEXT_REVIEW",
        "REQUIRE_IDENTITY_REVIEW",
    }
    assert report["contextual_truth_supported"] is False


def test_color_preservation_with_high_contradiction_risk_blocks():
    engine = ContextualTruthAuthorityEngine()

    report = engine.analyze(
        "color_preservation",
        truth_candidate_report={
            "contextual_truth_score": 0.72,
            "effective_contradiction": 0.24,
            "contradiction_threshold": 0.1,
            "contradiction_review_required": True,
            "contradiction_review_severity": "HIGH_RISK_REVIEW",
        },
        context_consistency_report={"context_consistency": 0.60},
        contextual_truth_report={
            "context_confidence": 0.60,
            "transfer_reliability": 0.42,
        },
        semantic_context_report={"confidence": 0.75},
        context_hierarchy_report={"score": 0.70},
        causal_validation_report={
            "causal_validation_score": 0.62,
            "causal_graph_alignment": 0.60,
            "dependency_coherence": 0.55,
            "contradiction_resistance": 0.35,
        },
    )

    assert report["contextual_truth_supported"] is False
    assert report["truth_governance_action"] in {
        "BLOCK_TRUTH_COMMIT",
        "REQUIRE_CAUSAL_REVIEW",
        "REQUIRE_MORE_CONTEXT_EVIDENCE",
    }
