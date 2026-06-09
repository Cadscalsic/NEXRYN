from core.causal import CounterfactualReasoner


def test_counterfactual_validation_detects_color_change_risk():
    reasoner = CounterfactualReasoner()

    report = reasoner.test(
        "color_preservation",
        {"color_behavior": "unchanged"},
    )

    assert report["requires_counterfactual_testing"] is False
    assert report["counterfactual_robustness"] == 0.8
    assert "color_behavior" in report["invalidating_factors"]


def test_counterfactual_validation_detects_identity_split_risk():
    reasoner = CounterfactualReasoner()

    report = reasoner.test(
        "object_identity_preservation",
        {
            "identity_behavior": "preserved",
            "object_count": "stable",
        },
    )

    assert report["requires_counterfactual_testing"] is True
    assert report["counterfactual_robustness"] == 0.6
    assert "identity_behavior" in report["invalidating_factors"]
    assert "object_count" in report["invalidating_factors"]
