from core.causal import ContextualTruthMapper, DependencyTracker


def test_contextual_truth_mapper_converts_absolute_truth_to_contextual_truth():
    tracker = DependencyTracker()
    dependencies = tracker.dependencies_for(
        "color_preservation",
        {"color_behavior": "color_reassigned"},
    )

    report = ContextualTruthMapper().map_truth(
        "color_preservation",
        {"color_behavior": "color_reassigned"},
        dependencies=dependencies,
        counterfactual_report={
            "counterfactual_robustness": 0.8,
            "invalidating_factors": ["color_behavior"],
        },
    )

    assert report["truth_type"] == "CONTEXTUAL_TRUTH"
    assert "color_behavior=color_reassigned" in report["invalid_contexts"]
    assert "counterfactual:color_behavior" in report["invalid_contexts"]
    assert report["transfer_reliability"] < 0.85


def test_contextual_truth_mapper_keeps_supported_truth_transferable():
    tracker = DependencyTracker()
    dependencies = tracker.dependencies_for(
        "shape_preservation",
        {"transformation_family": "duplication"},
    )

    report = ContextualTruthMapper().map_truth(
        "shape_preservation",
        {"transformation_family": "duplication"},
        dependencies=dependencies,
        counterfactual_report={
            "counterfactual_robustness": 1.0,
            "invalidating_factors": [],
        },
    )

    assert report["truth_type"] == "ABSOLUTE_TRUTH_CANDIDATE"
    assert report["context_transfer_reliability"] >= 0.85
