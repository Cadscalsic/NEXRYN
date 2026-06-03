from runtime.reflection.failure_analyzer import FailureAnalyzer


def test_high_accuracy_residual_mismatch_is_not_weak_semantic_abstraction():
    analyzer = FailureAnalyzer()

    analysis = analyzer.analyze_failure(
        {
            "reasoning": {"reasoning_depth": 4},
            "semantics": {"concept_count": 0},
            "routing": {"route_count": 2},
            "execution": {"node_count": 1},
        },
        {
            "success": False,
            "accuracy": 0.92,
        },
    )

    assert analysis["failure_causes"] == [
        "localized_prediction_mismatch",
    ]
    assert analysis["diagnostic_signals"] == [
        "low_semantic_density",
    ]
    assert analyzer.build_recovery_plan(analysis)["recovery_actions"] == [
        "inspect_residual_prediction_mismatch",
    ]


def test_weak_semantic_abstraction_requires_material_prediction_failure():
    analysis = FailureAnalyzer().analyze_failure(
        {
            "semantics": {"concept_count": 0},
        },
        {
            "success": False,
            "accuracy": 0.30,
        },
    )

    assert "severe_prediction_failure" in analysis["failure_causes"]
    assert "weak_semantic_abstraction" in analysis["failure_causes"]


def test_partial_success_uses_targeted_residual_refinement():
    analyzer = FailureAnalyzer()

    analysis = analyzer.analyze_failure(
        {},
        {
            "success": False,
            "success_state": "PARTIAL_SUCCESS",
            "partial_success": True,
            "accuracy": 0.96,
        },
    )

    assert analysis["failure_causes"] == [
        "partial_success_residual_mismatch",
    ]
    assert analyzer.build_recovery_plan(analysis)["recovery_actions"] == [
        "refine_partial_success_residual",
    ]


def test_semantic_density_uses_cognitive_cycle_semantic_graph():
    analysis = FailureAnalyzer().analyze_failure(
        {
            "semantics": {"concept_count": 11},
        },
        {
            "success": False,
            "accuracy": 0.92,
        },
    )

    assert analysis["semantic_density"] == 11
    assert "low_semantic_density" not in analysis["diagnostic_signals"]
