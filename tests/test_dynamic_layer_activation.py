from runtime.resource_governance import (
    AdaptiveExecutionGovernor,
    ActivationGuardLimits,
    CapabilityActivationRequest,
    ExecutionPolicyName,
    LayerState,
    RuntimeSignal,
    RuntimeSignalSeverity,
    RuntimeSignalType,
)


def signal(signal_type, execution_id="exec-1", payload=None, severity=RuntimeSignalSeverity.MEDIUM):
    return RuntimeSignal.create(
        execution_id=execution_id,
        task_id="task-1",
        signal_type=signal_type,
        source_layer="test_source",
        severity=severity,
        confidence=0.9,
        payload=payload or {},
    )


def test_runtime_signal_creation_and_consumption():
    governor = AdaptiveExecutionGovernor()
    runtime_signal = signal(RuntimeSignalType.COMPONENT_COUNT_CHANGED)

    governor.publish_signal(runtime_signal)
    consumed = governor.consume_signal(runtime_signal.signal_id, "test_consumed")

    assert consumed.consumed is True
    assert consumed.activation_effect == "test_consumed"
    assert governor.signal_monitor.get(runtime_signal.signal_id).signal_type == "COMPONENT_COUNT_CHANGED"


def test_on_demand_topology_activation_from_signal():
    governor = AdaptiveExecutionGovernor()

    governor.publish_signal(signal(RuntimeSignalType.TOPOLOGY_CHANGE_DETECTED))

    assert governor.get_layer_state("topology_reasoning") == LayerState.ACTIVE
    assert governor.can_execute("topology_reasoning") is True
    transition = governor.get_transition_history()[-1]
    assert transition["layer_name"] == "topology_reasoning"
    assert transition["trigger_signal"] == "TOPOLOGY_CHANGE_DETECTED"
    assert transition["approved"] is True


def test_capability_to_layer_resolution_and_manual_request():
    governor = AdaptiveExecutionGovernor()

    transition = governor.request_capability(
        "semantic_memory_integration",
        reason="semantic support requested",
        execution_id="exec-1",
    )

    assert transition.layer_name == "semantic_memory"
    assert transition.approved is True
    assert governor.get_layer_state("semantic_memory") == LayerState.ACTIVE


def test_dependency_activation_order_is_recorded():
    governor = AdaptiveExecutionGovernor()

    governor.publish_signal(signal(RuntimeSignalType.GRAVITY_SIGNAL_DETECTED))

    transition = governor.get_transition_history()[-1]
    assert transition["layer_name"] == "gravity_reasoning"
    assert transition["dependencies_activated"] == [
        "object_tracking",
        "spatial_reasoning",
    ]
    assert governor.get_layer_state("object_tracking") == LayerState.ACTIVE
    assert governor.get_layer_state("spatial_reasoning") == LayerState.ACTIVE


def test_dependency_cycle_rejection_is_explicit():
    governor = AdaptiveExecutionGovernor(register_defaults=False)
    governor.register_layer("layer_a", dependencies=("layer_b",))
    governor.register_layer("layer_b", dependencies=("layer_a",))

    transition = governor.request_capability("layer_a", execution_id="exec-1")

    assert transition.approved is False
    assert transition.rejection_reason == "DEPENDENCY_CYCLE"


def test_activation_loop_and_repeated_activation_are_prevented():
    governor = AdaptiveExecutionGovernor()
    runtime_signal = signal(RuntimeSignalType.TOPOLOGY_CHANGE_DETECTED)
    repeat_signal = signal(RuntimeSignalType.TOPOLOGY_CHANGE_DETECTED)

    governor.publish_signal(runtime_signal)
    governor.publish_signal(repeat_signal)

    rejection = governor.get_transition_history()[-1]
    assert rejection["approved"] is False
    assert rejection["rejection_reason"] in {
        "ACTIVATION_LOOP_DETECTED",
        "ACTIVATION_LIMIT_REACHED",
    }


def test_policy_blocked_activation_is_reported():
    governor = AdaptiveExecutionGovernor(execution_policy=ExecutionPolicyName.BALANCED)
    request = CapabilityActivationRequest(
        capability_name="diagnostic_probe",
        target_layer="diagnostic_probe",
        reason="diagnostic only request",
        trigger_signal="MANUAL_REQUEST",
        policy_constraints=("DIAGNOSTIC",),
    )

    transition = governor._activate_capability_request(request, "exec-1")

    assert transition.approved is False
    assert transition.rejection_reason == "POLICY_BLOCKED"


def test_layer_suspension_and_completion_states():
    governor = AdaptiveExecutionGovernor()
    governor.activate_layer("color_mapping")

    governor.suspend_layer("color_mapping", "no value produced", "exec-1")
    governor.complete_layer("semantic_compilation", "compiler finished")

    assert governor.get_layer_state("color_mapping") == LayerState.SUSPENDED
    assert governor.get_layer_state("semantic_compilation") == LayerState.COMPLETED


def test_escalation_from_light_to_balanced_then_deep():
    governor = AdaptiveExecutionGovernor()
    governor.create_initial_resource_plan("simple color remapping")

    governor.publish_signal(signal(RuntimeSignalType.CONFIDENCE_DROP))
    assert governor.get_current_strategy() == "BALANCED_EXECUTION"

    governor.publish_signal(signal(RuntimeSignalType.CONTRADICTION_DETECTED))
    assert governor.get_current_strategy() == "DEEP_EXECUTION"
    assert governor.escalation_controller.escalation_count == 2


def test_recovery_activation_from_localized_residual():
    governor = AdaptiveExecutionGovernor()

    governor.publish_signal(signal(RuntimeSignalType.LOCALIZED_RESIDUAL))

    assert governor.get_current_strategy() == "RECOVERY_EXECUTION"
    assert governor.get_layer_state("localized_repair") == LayerState.ACTIVE


def test_no_activation_after_exact_success():
    governor = AdaptiveExecutionGovernor()

    governor.publish_signal(signal(RuntimeSignalType.EXACT_SUCCESS))
    governor.publish_signal(signal(RuntimeSignalType.TOPOLOGY_CHANGE_DETECTED))

    rejection = governor.get_transition_history()[-1]
    assert rejection["approved"] is False
    assert rejection["rejection_reason"] == "TERMINAL_STATE_REACHED"
    assert governor.get_layer_state("topology_reasoning") == LayerState.REGISTERED


def test_explicit_activation_rejection_reporting_for_missing_layer():
    governor = AdaptiveExecutionGovernor(register_defaults=False)

    transition = governor.request_capability("missing_capability", execution_id="exec-1")
    report = governor.build_dynamic_activation_report()

    assert transition.approved is False
    assert transition.rejection_reason == "LAYER_NOT_REGISTERED"
    assert report["activation_rejections"][0]["rejection_reason"] == "LAYER_NOT_REGISTERED"


def test_invalid_execution_context_is_rejected():
    governor = AdaptiveExecutionGovernor()

    transition = governor.request_capability("topology_reasoning", execution_id="")

    assert transition.approved is False
    assert transition.rejection_reason == "INVALID_EXECUTION_CONTEXT"


def test_activation_limits_are_configurable():
    governor = AdaptiveExecutionGovernor()
    governor.activation_guard.limits = ActivationGuardLimits(max_activation_count_per_layer=0)

    transition = governor.request_capability("topology_reasoning", execution_id="exec-1")

    assert transition.approved is False
    assert transition.rejection_reason == "ACTIVATION_LIMIT_REACHED"


def test_dynamic_activation_report_and_transition_history_are_stable():
    governor = AdaptiveExecutionGovernor()
    governor.publish_signal(signal(RuntimeSignalType.SPATIAL_RELATION_DETECTED))
    governor.publish_signal(signal(RuntimeSignalType.LAYER_NO_VALUE_PRODUCED, payload={"layer_name": "spatial_reasoning"}))

    history = governor.get_transition_history()
    report = governor.build_dynamic_activation_report(diagnostic=True)
    rendered = governor.render_dynamic_activation_report()

    assert history[0]["layer_name"] == "spatial_reasoning"
    assert report["DYNAMIC_RESOURCE_ACTIVATION_REPORT"] is True
    assert report["runtime_signals_received"] == 2
    assert report["layers_suspended"][0]["layer_name"] == "spatial_reasoning"
    assert "DYNAMIC RESOURCE ACTIVATION REPORT" in rendered
    assert "signal_ledger" in report
