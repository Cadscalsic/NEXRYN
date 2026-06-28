from runtime.routing import PreReasoningRouter, build_task_profile


def _color_mapping_task():
    return {
        "task_id": "color_mapping_fixture",
        "input_grid": [
            [0, 1],
            [0, 0],
        ],
        "output_grid": [
            [0, 2],
            [0, 0],
        ],
    }


def test_task_profile_detects_color_mapping():
    profile = build_task_profile(_color_mapping_task())

    assert profile["task_family"] == "color_mapping"
    assert profile["requires_color_mapping"] is True
    assert profile["requires_truth_promotion"] is False
    assert profile["confidence"] >= 0.8


def test_color_mapping_task_skips_truth_commit():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(profile, {"mode": "fast"})

    assert "truth_commit" in plan["disabled_layers"] or "truth_commit" in plan["deferred_layers"]
    assert router.should_run("truth_commit", profile, {"pre_reasoning_execution_plan": plan}) is False


def test_simple_transformation_skips_deep_governance():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(profile, {"mode": "fast"})

    assert "deep_governance" in plan["disabled_layers"] or "deep_governance" in plan["deferred_layers"]
    assert plan["execution_mode"] == "selective"


def test_unknown_complex_enables_context_discovery():
    router = PreReasoningRouter()
    profile = router.analyze_task({"task_id": "unknown"})
    plan = router.build_execution_plan(profile, {"mode": "adaptive"})

    assert profile["task_family"] == "unknown_complex"
    assert "context_discovery" in plan["enabled_layers"]


def test_new_concept_enables_dependency_reasoning():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(
        profile,
        {"mode": "fast", "new_concept_detected": True},
    )

    assert "dependency_reasoning" in plan["enabled_layers"]


def test_truth_candidate_does_not_run_without_valid_context():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(profile, {"mode": "fast"})

    assert router.should_run("truth_candidate", profile, {"pre_reasoning_execution_plan": plan}) is False


def test_disabled_layer_returns_skipped_report():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(profile, {"mode": "fast"})
    report = router.skipped_report("truth_commit", plan)

    assert report["report_state"] == "skipped"
    assert report["skipped"] is True
    assert report["skip_reason"] in {
        "not_required_by_task_profile",
        "deferred_by_selective_execution",
    }


def test_no_empty_report_is_printed_without_report_state():
    router = PreReasoningRouter()
    report = router.skipped_report("context_hierarchy", {})

    assert report
    assert "report_state" in report


def test_fast_mode_uses_aggressive_selective_plan():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(profile, {"mode": "fast"})

    assert plan["execution_mode"] == "selective"
    assert len(plan["disabled_layers"]) + len(plan["deferred_layers"]) >= 4
    assert router.report()["full_stack_avoided"] is True


def test_deep_mode_can_run_full_stack():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(profile, {"mode": "deep"})

    assert plan["execution_mode"] == "full"
    assert "truth_commit" in plan["enabled_layers"]
    assert "deep_governance" in plan["enabled_layers"]


def test_safety_override_enables_governance():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    plan = router.build_execution_plan(
        profile,
        {"mode": "fast", "safety_risk_detected": True},
    )

    assert "deep_governance" in plan["enabled_layers"]
    assert "safety_risk" in plan["safety_overrides"]


def test_structural_capability_forces_dependency_reasoning_in_fast_mode():
    router = PreReasoningRouter()
    profile = router.analyze_task(
        _color_mapping_task(),
        {
            "required_capabilities": [
                "color_analysis",
                "topology_preservation",
            ],
            "suspected_concepts": [
                "shape_preservation",
                "symmetry_preservation",
                "symbolic_remapping",
                "topological_growth",
            ],
        },
    )
    plan = router.build_execution_plan(profile, {"mode": "fast"})

    assert "dependency_reasoning" in plan["enabled_layers"]
    assert "context_discovery" in plan["enabled_layers"]
    assert plan["dependency_reasoning_enabled"] is True
    assert plan["dependency_activation_attempted"] is True
    assert plan["dependency_activation_blocked"] is False
    assert plan["router_decision_trace"]["escalation_level"] in {
        "LEVEL_4",
        "LEVEL_5",
        "LEVEL_6",
    }


def test_low_confidence_escalates_dependency_and_context():
    router = PreReasoningRouter()
    profile = router.analyze_task(_color_mapping_task())
    profile["confidence"] = 0.65
    profile["suspected_concepts"] = ["color_mapping"]
    profile["required_capabilities"] = [
        "color_analysis",
        "transformation_solver",
        "evaluation",
    ]
    plan = router.build_execution_plan(profile, {"mode": "adaptive"})

    assert profile["confidence"] < 0.70
    assert "dependency_reasoning" in plan["enabled_layers"]
    assert "context_discovery" in plan["enabled_layers"]
    assert plan["decision_reason"] == "low_router_confidence_escalates_reasoning"


def test_router_decision_trace_audits_required_fields():
    router = PreReasoningRouter()
    profile = router.analyze_task(
        {
            **_color_mapping_task(),
            "task_description":
            "symbolic_remapping with propagation and topology preservation",
        }
    )
    plan = router.build_execution_plan(profile, {"mode": "fast"})
    trace = plan["router_decision_trace"]

    for key in [
        "detected_family",
        "detected_capabilities",
        "enabled_layers",
        "disabled_layers",
        "deferred_layers",
        "dependency_reasoning_enabled",
        "context_discovery_enabled",
        "truth_candidate_enabled",
        "truth_commit_enabled",
        "router_confidence",
        "decision_reason",
    ]:
        assert key in trace
    assert trace["dependency_reasoning_enabled"] is True
