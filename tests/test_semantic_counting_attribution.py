from runtime.semantics.semantic_abstraction import SemanticAbstractionEngine


def test_task_identity_attributes_object_counting_family():
    engine = SemanticAbstractionEngine()

    concepts = engine._concepts_from_spatial_signals(
        "arc_concept_object_counting_03.json"
    )

    assert "object_counting" in concepts
    assert "cardinality" in concepts
    assert "quantity_preservation" in concepts
    assert "quantity_transformation" in concepts
    assert "numerical_reasoning" in concepts
    assert "set_reasoning" in concepts
