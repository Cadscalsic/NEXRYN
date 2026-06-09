from core.context import ContextBindingEngine


def test_context_binding_explains_shape_preservation_under_duplication():
    engine = ContextBindingEngine()

    report = engine.bind(
        "shape_preservation",
        context_report={
            "transformation_family": "duplication",
            "topology_behavior": "topology_splitting",
            "identity_behavior": "identity_split",
        },
        semantic_context_report={
            "properties": ["preserves_shape", "creates_objects"],
            "capabilities": ["structural_replication"],
            "confidence": 0.9,
        },
        context_hierarchy_report={"context_hierarchy_score": 0.94},
        contextual_truth_report={"contextual_truth_score": 0.65},
        causal_validation_report={"validation_score": 0.85},
    )

    assert report["system"] == "context_binding_engine"
    assert report["binding_state"] == "CONTEXT_BOUND"
    assert report["context_binding_score"] >= 0.75
    assert (
        "duplication -> structural_replication -> "
        "preserves_shape -> shape_preservation"
    ) in report["why_valid"]


def test_context_binding_keeps_unexplained_truth_under_review():
    engine = ContextBindingEngine()

    report = engine.bind(
        "position_preservation",
        context_report={"transformation_family": "duplication"},
        semantic_context_report={
            "properties": ["preserves_shape"],
            "confidence": 0.9,
        },
    )

    assert report["binding_state"] != "CONTEXT_BOUND"
    assert report["why_valid"] == []
