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


def test_context_signal_text_does_not_inline_large_context_payloads():
    engine = SemanticAbstractionEngine()

    signal = engine._context_signal_text({
        "task_path": "arc_concept_object_counting_03.json",
        "enabled_tools": [f"tool_{index}" for index in range(100)],
        "task_profile": {
            "required_capabilities": {
                f"capability_{index}": "x" * 500
                for index in range(100)
            },
        },
    })

    assert len(signal) <= 2000
    assert "object_counting" in signal
    assert "x" * 200 not in signal
