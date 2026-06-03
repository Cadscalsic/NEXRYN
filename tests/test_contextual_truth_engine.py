from core.truth.contextual_truth_engine import ContextualTruthEngine


def test_contextual_truth_engine_models_preservation_as_conditional():
    engine = ContextualTruthEngine()
    report = engine.contextual_truth_model(
        "color_preservation",
        {
            "active_concepts": ["color_transform"],
        },
    )

    assert report["truth_type"] == "conditional"
    assert report["conditional_form"] == "IF no_color_transform: color_preservation"
    assert report["truth_condition"] == "no_color_transform"
    assert report["active_transform_context"] is True


def test_contextual_truth_engine_detects_symbolic_remapping_as_color_transform_context():
    engine = ContextualTruthEngine()
    report = engine.contextual_truth_model(
        "color_preservation",
        {
            "active_concepts": ["symbolic_remapping"],
        },
    )

    assert report["truth_type"] == "conditional"
    assert report["active_transform_context"] is True


def test_contextual_truth_engine_detects_shape_transformation_as_shape_transform_context():
    engine = ContextualTruthEngine()
    report = engine.contextual_truth_model(
        "shape_preservation",
        {
            "active_concepts": ["shape_transformation"],
        },
    )

    assert report["truth_type"] == "conditional"
    assert report["active_transform_context"] is True


def test_contextual_truth_engine_detects_symmetry_reasoning_as_symmetry_transform_context():
    engine = ContextualTruthEngine()
    report = engine.contextual_truth_model(
        "symmetry_preservation",
        {
            "active_concepts": ["symmetry_reasoning"],
        },
    )

    assert report["truth_type"] == "conditional"
    assert report["active_transform_context"] is True


def test_contextual_truth_engine_detects_attribute_remapping_as_color_transform_context():
    engine = ContextualTruthEngine()
    report = engine.contextual_truth_model(
        "color_preservation",
        {
            "active_concepts": ["attribute_remapping"],
        },
    )

    assert report["truth_type"] == "conditional"
    assert report["active_transform_context"] is True


def test_contextual_truth_engine_detects_grow_topology_as_topology_transform_context():
    engine = ContextualTruthEngine()
    report = engine.contextual_truth_model(
        "topology_preservation",
        {
            "active_concepts": ["grow_topology"],
        },
    )

    assert report["truth_type"] == "conditional"
    assert report["active_transform_context"] is True
