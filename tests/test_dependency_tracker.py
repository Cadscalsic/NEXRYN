from core.causal import DependencyTracker


def test_dependency_tracker_reports_validated_and_missing_links():
    tracker = DependencyTracker()

    report = tracker.report(
        "color_preservation",
        {"color_behavior": "unchanged"},
    )

    assert report["dependency_coherence"] == 1.0
    assert report["missing_links"] == []
    assert report["validated_links"][0]["dependency"] == "color_behavior"
    assert report["dependency_chain"] == [
        "color_preservation",
        "color_behavior",
    ]


def test_dependency_tracker_detects_contextual_truth_requirement():
    tracker = DependencyTracker()

    report = tracker.report(
        "color_preservation",
        {"color_behavior": "color_reassigned"},
    )

    assert report["dependency_coherence"] == 0.5
    assert report["missing_links"][0]["relation"] == "context_requires"
    assert report["dependency_chain"] == [
        "color_preservation",
        "color_behavior",
        "contextual_truth_required",
    ]
