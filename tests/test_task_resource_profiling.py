from runtime.resource_governance import (
    AdaptiveExecutionGovernor,
    ExecutionStrategy,
    LayerState,
    TaskProfiler,
)


def test_simple_color_remapping_profile_prefers_light_capabilities():
    profile = TaskProfiler().profile("simple color remapping replace red with blue")

    assert profile.task_complexity == "LOW"
    assert "object_tracking" in profile.expected_capabilities
    assert "color_mapping" in profile.expected_capabilities
    assert "semantic_compilation" in profile.potential_capabilities
    assert "topology_reasoning" in profile.not_required_capabilities
    assert "gravity_reasoning" in profile.not_required_capabilities


def test_rotation_scaling_profile_detects_transformation_family():
    governor = AdaptiveExecutionGovernor(register_defaults=False)
    resource_plan = governor.create_initial_resource_plan("rotation and scaling of one object")

    assert resource_plan.execution_strategy == ExecutionStrategy.BALANCED_EXECUTION
    assert "object_tracking" in resource_plan.execution_plan.required_layers
    assert "transformation_reasoning" in resource_plan.execution_plan.active_layers
    assert "semantic_compilation" in resource_plan.execution_plan.active_layers
    assert "spatial_reasoning" in resource_plan.execution_plan.on_demand_layers
    assert "topology_reasoning" in resource_plan.execution_plan.blocked_layers


def test_gravity_task_profile_marks_spatial_and_gravity_capabilities():
    governor = AdaptiveExecutionGovernor(register_defaults=False)
    resource_plan = governor.create_initial_resource_plan("gravity simulation: objects fall onto support")

    assert "object_tracking" in resource_plan.execution_plan.required_layers
    assert "spatial_reasoning" in resource_plan.execution_plan.active_layers
    assert "gravity_reasoning" in resource_plan.execution_plan.active_layers
    assert "topology_reasoning" in resource_plan.execution_plan.on_demand_layers
    assert resource_plan.task_profile.estimated_execution_cost in {"LOW", "MEDIUM", "HIGH"}


def test_initial_resource_planning_does_not_mutate_governor_layer_states():
    governor = AdaptiveExecutionGovernor()
    before = governor.layer_states()

    governor.create_initial_resource_plan("simple color remapping")

    assert governor.layer_states() == before
    assert governor.get_layer_state("object_tracking") == LayerState.REGISTERED
    assert governor.can_execute("object_tracking") is False


def test_task_resource_profile_report_exposes_required_sections():
    governor = AdaptiveExecutionGovernor(register_defaults=False)
    report = governor.build_task_resource_profile_report(
        "ambiguous topology graph dependency task with unknown concept"
    )
    rendered = governor.render_task_resource_profile_report(
        "ambiguous topology graph dependency task with unknown concept"
    )

    assert report["TASK_RESOURCE_PROFILE_REPORT"] is True
    assert report["task_complexity"] in {"MEDIUM", "HIGH", "EXTREME"}
    assert report["execution_strategy"] in {
        "BALANCED_EXECUTION",
        "DEEP_EXECUTION_REQUIRED",
        "UNCERTAIN_EXECUTION",
    }
    assert report["estimated_costs"]["expected_execution_cost"] in {
        "LOW",
        "MEDIUM",
        "HIGH",
        "EXTREME",
    }
    assert "TASK RESOURCE PROFILE REPORT" in rendered
