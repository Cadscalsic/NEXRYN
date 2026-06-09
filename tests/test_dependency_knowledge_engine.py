from core.causal import DependencyKnowledgeEngine


def sample_color_report():
    engine = DependencyKnowledgeEngine()
    return engine.analyze(
        concept="color_preservation",
        context_report={
            "transformation": "duplication",
            "color": "color_reassigned",
            "topology": "topology_splitting",
            "identity": "identity_split",
        },
        semantic_context_report={
            "context": "duplication",
            "properties": [
                "changes_color",
                "creates_objects",
                "modifies_identity",
                "modifies_topology",
                "preserves_shape",
            ],
            "confidence": 0.9,
        },
        causal_validation_report={
            "causal_graph_alignment": 0.81,
            "causal_validation_score": 0.80,
            "dependency_coherence": 0.66,
            "context_consistency": 0.5,
            "identity_compatibility": 1.0,
        },
        truth_candidate_report={
            "effective_contradiction": 0.13,
            "contradiction_threshold": 0.1,
            "contradiction_review_required": True,
        },
    )


def test_dependency_extraction_detects_required_concept_dependency():
    engine = DependencyKnowledgeEngine()

    dependencies = engine.extract_dependencies(
        "color_preservation",
        context_report={"color": "color_reassigned"},
    )

    assert dependencies[0]["dependency"] == "color_behavior"
    assert dependencies[0]["value"] == "color_reassigned"
    assert dependencies[0]["required"] is True


def test_dependency_classification_marks_identity_and_contradiction():
    engine = DependencyKnowledgeEngine()

    identity = engine.classify_dependency({
        "concept": "object_identity_preservation",
        "dependency": "identity_behavior",
        "relation": "depends_on",
        "value": "identity_split",
        "required": True,
    })
    contradiction = engine.classify_dependency({
        "concept": "color_preservation",
        "dependency": "contradiction_review",
        "relation": "invalidates",
        "value": True,
        "required": True,
        "evidence": {"contradiction_review_required": True},
    })

    assert "identity_dependency" in identity["dependency_types"]
    assert "hard_dependency" in identity["dependency_types"]
    assert "contradiction_dependency" in contradiction["dependency_types"]


def test_dependency_scoring_uses_safe_defaults():
    engine = DependencyKnowledgeEngine()
    dependency = engine.classify_dependency({
        "concept": "shape_preservation",
        "dependency": "structural_integrity",
        "relation": "depends_on",
        "value": None,
        "required": True,
    })

    scores = engine.score_dependency(dependency)

    assert 0.0 <= scores["dependency_confidence"] <= 1.0
    assert scores["transferability"] == 0.4
    assert scores["contradiction_resistance"] == 1.0


def test_missing_dependency_detection_for_color_preservation():
    engine = DependencyKnowledgeEngine()
    dependencies = engine.extract_dependencies(
        "color_preservation",
        context_report={"color": "color_reassigned"},
    )

    missing = engine.identify_missing_dependencies(
        "color_preservation",
        dependencies,
    )

    assert "color_mapping_rule" in missing
    assert "recolor_condition" in missing
    assert "color_behavior" not in missing


def test_coherence_computation_and_action_recommendation():
    engine = DependencyKnowledgeEngine()
    dependency = engine.classify_dependency({
        "concept": "shape_preservation",
        "dependency": "structural_integrity",
        "relation": "depends_on",
        "value": "duplication",
        "required": True,
        "evidence": {"support_score": 1.0, "dependency_coherence": 0.9},
    })
    engine.score_dependency(dependency)
    dependency["validation"] = engine.validate_dependency(dependency)

    coherence = engine.compute_dependency_coherence([dependency])
    report = engine.build_report(
        "shape_preservation",
        [dependency],
        [],
        coherence,
    )

    assert coherence > 0.8
    assert report["recommended_action"] == "PROMOTE_TRUTH"


def test_graceful_behavior_with_empty_reports():
    engine = DependencyKnowledgeEngine()

    report = engine.analyze("unknown_concept")

    assert report["system"] == "dependency_knowledge_engine"
    assert report["dependency_coherence"] == 0.0
    assert report["recommended_action"] in {
        "REQUIRE_CAUSAL_REVIEW",
        "HOLD_FOR_MORE_EVIDENCE",
    }


def test_color_preservation_under_duplication_context_requires_contextual_truth():
    report = sample_color_report()

    assert report["concept"] == "color_preservation"
    assert "color_mapping_rule" in report["missing_dependencies"]
    assert "recolor_condition" in report["missing_dependencies"]
    assert report["recommended_action"] == "REQUIRE_CONTEXTUAL_TRUTH"
    assert report["dependency_coherence"] >= 0.65


def test_shape_preservation_under_unknown_context_holds_for_more_evidence():
    engine = DependencyKnowledgeEngine()

    report = engine.analyze("shape_preservation")

    assert "structural_integrity" in report["missing_dependencies"]
    assert "shape_equivalence" in report["missing_dependencies"]
    assert report["recommended_action"] in {
        "HOLD_FOR_MORE_EVIDENCE",
        "BLOCK_TRUTH_COMMIT",
        "REQUIRE_CAUSAL_REVIEW",
    }
    assert report["dependency_coherence"] < 0.8


def test_memory_reinforces_existing_dependency():
    engine = DependencyKnowledgeEngine()

    first = engine.analyze(
        "position_preservation",
        context_report={"position": "aligned"},
    )
    second = engine.analyze(
        "position_preservation",
        context_report={"position": "aligned"},
    )
    dependency = second["dependencies"][0]

    assert first["dependencies"][0]["memory"]["evidence_count"] == 1
    assert dependency["memory"]["evidence_count"] == 2
