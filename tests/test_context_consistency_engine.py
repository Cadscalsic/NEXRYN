from core.context import ContextConsistencyEngine


def color_inputs():
    return {
        "context_report": {
            "transformation": "duplication",
            "topology": "topology_splitting",
            "color": "color_reassigned",
            "identity": "identity_split",
            "confidence": 0.76,
            "cluster": "Structural Transformation",
        },
        "semantic_context_report": {
            "context": "duplication",
            "properties": [
                "changes_color",
                "creates_objects",
                "modifies_identity",
                "modifies_topology",
                "preserves_shape",
            ],
            "capabilities": [
                "attribute_remapping",
                "object_creation",
                "structural_replication",
                "structure_preservation",
            ],
            "constraints": [
                "color_mapping_changes",
                "identity_continuity_may_split",
            ],
            "implications": [
                "color_change",
                "object_count_increase",
                "shape_preservation_expected",
            ],
            "confidence": 0.9,
        },
        "contextual_truth_report": {
            "valid_contexts": [
                "task_cluster:duplication|transformation_family:duplication|object_count:2|topology_behavior:topology_splitting|color_behavior:color_reassigned|identity_behavior:identity_split"
            ],
            "invalid_contexts": [],
            "context_confidence": 0.82,
            "transfer_reliability": 0.44,
            "status": "CONTEXT_REVIEW_REQUIRED",
        },
    }


def test_context_normalization():
    engine = ContextConsistencyEngine()
    inputs = color_inputs()

    normalized = engine.normalize_context(**inputs)

    assert normalized["transformation_family"] == "duplication"
    assert normalized["task_cluster"] == "Structural Transformation"
    assert normalized["topology_behavior"] == "topology_splitting"
    assert normalized["color_behavior"] == "color_reassigned"
    assert normalized["identity_behavior"] == "identity_split"
    assert "changes_color" in normalized["semantic_properties"]
    assert normalized["confidence"] == 0.9


def test_expected_context_profiles():
    engine = ContextConsistencyEngine()

    profile = engine.expected_context_profile("shape_preservation")

    assert "shape_equivalence" in profile["expected_dependencies"]
    assert "structural_integrity" in profile["expected_dependencies"]


def test_support_scoring_for_shape_under_duplication():
    engine = ContextConsistencyEngine()
    normalized = engine.normalize_context(
        context_report={
            "transformation": "duplication",
            "topology": "topology_splitting",
            "size": "size_preserved",
            "confidence": 0.9,
        },
        semantic_context_report={
            "properties": ["preserves_shape"],
            "capabilities": ["structural_replication"],
            "confidence": 0.9,
        },
    )

    assert engine.score_context_support("shape_preservation", normalized) > 0.85


def test_transferability_scoring():
    engine = ContextConsistencyEngine()
    normalized = engine.normalize_context(
        context_report={"transformation": "duplication"},
    )

    score = engine.score_context_transferability(
        "shape_preservation",
        {
            "valid_contexts": [engine._context_signature(normalized)],
            "invalid_contexts": [],
            "context_confidence": 0.9,
            "transfer_reliability": 0.9,
        },
        normalized,
    )

    assert score > 0.85


def test_specificity_scoring():
    engine = ContextConsistencyEngine()
    specific = engine.normalize_context(**color_inputs())
    unknown = engine.normalize_context()

    specific_report = engine.score_context_specificity(
        "color_preservation",
        specific,
    )
    unknown_report = engine.score_context_specificity(
        "color_preservation",
        unknown,
    )

    assert specific_report["specificity_state"] == "HIGHLY_CONTEXT_BOUND"
    assert unknown_report["specificity_state"] == "UNDERDETERMINED"


def test_stability_scoring_uses_history():
    engine = ContextConsistencyEngine()
    normalized = engine.normalize_context(
        context_report={"transformation": "duplication"},
    )
    engine.update_memory("shape_preservation", normalized, 0.82)
    engine.update_memory("shape_preservation", normalized, 0.84)

    stability = engine.score_context_stability(
        "shape_preservation",
        normalized,
    )

    assert stability > 0.80


def test_mismatch_detection():
    engine = ContextConsistencyEngine()
    normalized = engine.normalize_context(
        context_report={"color": "color_reassigned"},
        semantic_context_report={"properties": ["changes_color"]},
    )

    mismatch = engine.detect_context_mismatch(
        "color_preservation",
        normalized,
    )

    assert mismatch["mismatch_detected"] is True
    assert mismatch["mismatch_reasons"] == [
        "color_reassigned_without_mapping_rule"
    ]


def test_final_consistency_computation():
    engine = ContextConsistencyEngine()

    score = engine.compute_context_consistency(
        support_score=0.8,
        transferability_score=0.7,
        specificity_report={
            "specificity_state": "CONTEXT_SPECIFIC",
            "specificity_score": 0.6,
        },
        stability_score=0.8,
        mismatch_report={"mismatch_detected": False},
    )

    assert score == 0.815


def test_action_recommendation():
    engine = ContextConsistencyEngine()

    assert engine.recommend_action(
        0.90,
        {"mismatch_detected": False, "mismatch_reasons": []},
        {"specificity_state": "GENERAL"},
    ) == "COMMIT_TRUTH"
    assert engine.recommend_action(
        0.80,
        {"mismatch_detected": False, "mismatch_reasons": []},
        {"specificity_state": "CONTEXT_SPECIFIC"},
    ) == "COMMIT_CONTEXTUAL_TRUTH"
    assert engine.recommend_action(
        0.60,
        {"mismatch_detected": False, "mismatch_reasons": []},
        {"specificity_state": "CONTEXT_SPECIFIC"},
    ) == "HOLD_FOR_CONTEXT_REVIEW"
    assert engine.recommend_action(
        0.70,
        {
            "mismatch_detected": True,
            "mismatch_reasons": ["color_reassigned_without_mapping_rule"],
        },
        {"specificity_state": "CONTEXT_SPECIFIC"},
    ) == "REQUIRE_MAPPING_RULE"


def test_graceful_behavior_with_empty_reports():
    engine = ContextConsistencyEngine()

    report = engine.analyze("unknown_concept")

    assert report["system"] == "context_consistency_engine"
    assert report["context_specificity"]["specificity_state"] == "UNDERDETERMINED"
    assert report["recommended_action"] in {
        "REQUIRE_CONTEXT_DISCOVERY",
        "BLOCK_TRUTH_COMMIT",
    }


def test_color_preservation_with_color_reassigned():
    engine = ContextConsistencyEngine()
    inputs = color_inputs()

    report = engine.analyze("color_preservation", **inputs)

    assert report["context_mismatch"]["mismatch_detected"] is False
    assert report["context_specificity"]["specificity_state"] == (
        "HIGHLY_CONTEXT_BOUND"
    )
    assert report["context_consistency"] >= 0.55
    assert report["recommended_action"] in {
        "COMMIT_CONTEXTUAL_TRUTH",
        "HOLD_FOR_CONTEXT_REVIEW",
    }


def test_context_consistency_uses_scene_graph_evidence():
    engine = ContextConsistencyEngine()

    baseline = engine.analyze(
        "shape_preservation",
        context_report={"transformation": "duplication", "confidence": 0.76},
        semantic_context_report={
            "properties": ["preserves_shape"],
            "capabilities": ["structural_replication"],
            "confidence": 0.9,
        },
    )
    scene_supported = engine.analyze(
        "shape_preservation",
        context_report={"transformation": "duplication", "confidence": 0.76},
        semantic_context_report={
            "properties": ["preserves_shape"],
            "capabilities": ["structural_replication"],
            "confidence": 0.9,
        },
        scene_graph_report={
            "summary": {
                "object_level_ready": True,
                "input_object_count": 1,
                "output_object_count": 2,
            },
            "object_matches": [{
                "shape_preserved": True,
            }],
            "object_events": [{
                "event": "object_added",
                "confidence": 0.82,
            }],
            "relation_changes": {
                "relations_added": ["left_of"],
                "relations_preserved": ["same_shape"],
            },
        },
    )

    assert scene_supported["scene_graph_consistency"] > 0.0
    assert scene_supported["context_consistency"] > baseline[
        "context_consistency"
    ]


def test_color_preservation_requires_mapping_rule_without_mapping_signal():
    engine = ContextConsistencyEngine()

    report = engine.analyze(
        "color_preservation",
        context_report={"color": "color_reassigned", "confidence": 0.8},
        semantic_context_report={"properties": ["changes_color"]},
    )

    assert report["recommended_action"] == "REQUIRE_MAPPING_RULE"


def test_object_identity_preservation_with_identity_split():
    engine = ContextConsistencyEngine()

    report = engine.analyze(
        "object_identity_preservation",
        context_report={"identity": "identity_split", "confidence": 0.8},
        semantic_context_report={"properties": ["modifies_identity"]},
    )

    assert report["context_mismatch"]["mismatch_detected"] is True
    assert report["recommended_action"] == "REQUIRE_IDENTITY_LINEAGE"


def test_topology_preservation_with_topology_splitting():
    engine = ContextConsistencyEngine()

    report = engine.analyze(
        "topology_preservation",
        context_report={"topology": "topology_splitting", "confidence": 0.8},
        semantic_context_report={"properties": ["modifies_topology"]},
    )

    assert report["context_mismatch"]["mismatch_detected"] is True
    assert report["recommended_action"] == "HOLD_FOR_CONTEXT_REVIEW"
