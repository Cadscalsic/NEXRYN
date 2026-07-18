from runtime.capability_architecture import (
    ActivationContract,
    ActivationType,
    CapabilityCategory,
    CapabilityContract,
    CapabilityGovernor,
    CapabilityHealthStatus,
    CapabilityLifecycleState,
    DependencyContract,
    HealthContract,
    InputContract,
    LayerDescriptor,
    OutputContract,
)
from runtime.resource_governance.adaptive_execution_governor import AdaptiveExecutionGovernor
from runtime.resource_governance.execution_policy import ExecutionPolicyName


def capability(
    name="topology_reasoning",
    owner="TopologyReasoningLayer",
    category=CapabilityCategory.COGNITIVE_REASONING,
    deps=(),
    policies=None,
    activation_type=ActivationType.ON_DEMAND,
    health=None,
    outputs=("hypotheses",),
):
    policies = policies or (
        ExecutionPolicyName.BALANCED,
        ExecutionPolicyName.MAX_ACCURACY,
        ExecutionPolicyName.DIAGNOSTIC,
    )
    return CapabilityContract(
        capability_id=f"cap::{name}",
        capability_name=name,
        capability_version="1.0",
        owning_layer=owner,
        category=category,
        description=f"{name} capability",
        activation_type=activation_type,
        dependency_contract=DependencyContract(capability_dependencies=tuple(deps)),
        input_contract=InputContract(required_inputs=("grid_objects",)),
        output_contract=OutputContract(produced_outputs=tuple(outputs)),
        activation_contract=ActivationContract(
            activation_type=activation_type,
            activation_signals=("TOPOLOGY_CHANGE_DETECTED",),
            execution_policies=tuple(policies),
            required_budget_types=("active_compute_seconds",),
        ),
        health_contract=health or HealthContract(),
        policy_permissions=tuple(policies),
    )


def layer(name="TopologyReasoningLayer", caps=("topology_reasoning",), legacy="NATIVE"):
    return LayerDescriptor(
        layer_id=f"layer::{name}",
        layer_name=name,
        capabilities=tuple(caps),
        legacy_status=legacy,
    )


def test_capability_and_layer_registration():
    governor = CapabilityGovernor()

    assert governor.register_layer(layer()) is True
    result = governor.register_capability(capability())

    assert result.valid is True
    assert governor.discovery.get_capability("topology_reasoning").owning_layer == "TopologyReasoningLayer"
    assert governor.discovery.get_layer("TopologyReasoningLayer").layer_name == "TopologyReasoningLayer"


def test_ownership_validation_rejects_duplicate_owner_conflict():
    governor = CapabilityGovernor()
    governor.register_layer(layer())
    governor.register_capability(capability())

    conflict = governor.register_capability(capability(owner="OtherLayer"))

    assert conflict.valid is False
    assert "OWNERSHIP_CONFLICT" in conflict.errors
    assert governor.build_report()["ownership_conflicts"] == 1


def test_dependency_validation_rejects_missing_dependency():
    governor = CapabilityGovernor()
    governor.register_layer(layer(caps=("topology_execution",)))

    result = governor.register_capability(capability("topology_execution", deps=("spatial_reasoning",)))

    assert result.valid is False
    assert "DEPENDENCY_NOT_REGISTERED" in result.errors


def test_dependency_validation_passes_when_dependency_registered_first():
    governor = CapabilityGovernor()
    governor.register_layer(layer("SpatialLayer", ("spatial_reasoning",)))
    governor.register_capability(capability("spatial_reasoning", owner="SpatialLayer"))
    governor.register_layer(layer("TopologyExecutionLayer", ("topology_execution",)))

    result = governor.register_capability(capability("topology_execution", owner="TopologyExecutionLayer", deps=("spatial_reasoning",)))

    assert result.valid is True
    assert governor.discovery.find_dependencies("topology_execution") == ("spatial_reasoning",)


def test_io_activation_health_and_compatibility_validation():
    governor = CapabilityGovernor()
    governor.register_layer(layer(caps=("bad_io",)))
    bad_io = capability("bad_io", outputs=())
    bad_health = capability(
        "blocked_capability",
        owner="BlockedLayer",
        health=HealthContract(health_status=CapabilityHealthStatus.BLOCKED),
    )

    io_result = governor.register_capability(bad_io)
    health_result = governor.register_capability(bad_health)

    assert "OUTPUT_CONTRACT_EMPTY" in io_result.errors
    assert "HEALTH_NOT_ACTIVATABLE" in health_result.errors


def test_policy_permissions_gate_capability_activation():
    governor = CapabilityGovernor()
    governor.register_layer(layer("DiagnosticLayer", ("diagnostic_profiler",)))
    governor.register_capability(capability(
        "diagnostic_profiler",
        owner="DiagnosticLayer",
        category=CapabilityCategory.DIAGNOSTIC,
        policies=(ExecutionPolicyName.DIAGNOSTIC,),
        activation_type=ActivationType.DIAGNOSTIC_ONLY,
    ))

    assert governor.can_activate_capability("diagnostic_profiler", ExecutionPolicyName.BALANCED) is False
    assert governor.can_activate_capability("diagnostic_profiler", ExecutionPolicyName.DIAGNOSTIC) is True


def test_capability_categories_and_discovery_apis():
    governor = CapabilityGovernor()
    governor.register_layer(layer("MemoryLayer", ("semantic_memory",)))
    governor.register_capability(capability(
        "semantic_memory",
        owner="MemoryLayer",
        category=CapabilityCategory.MEMORY,
        activation_type=ActivationType.ON_DEMAND,
    ))

    assert governor.discovery.find_capabilities_by_category("MEMORY")[0].capability_name == "semantic_memory"
    assert governor.discovery.find_capabilities_by_signal("TOPOLOGY_CHANGE_DETECTED")
    assert governor.discovery.find_capabilities_by_policy(ExecutionPolicyName.BALANCED)
    assert governor.discovery.find_capabilities_by_activation_type("ON_DEMAND")
    assert governor.discovery.find_capability_owner("semantic_memory") == "MemoryLayer"


def test_legacy_layer_adaptation_preserves_backward_compatibility():
    governor = CapabilityGovernor()

    result = governor.register_legacy_layer("legacy_semantic_memory", "semantic_memory_integration")
    report = governor.build_report()

    assert result.valid is True
    assert report["legacy_layers"] == 1
    assert governor.discovery.get_capability("semantic_memory_integration").compatibility["legacy_adapter"] is True


def test_capability_lifecycle_transitions_are_governed():
    governor = CapabilityGovernor()
    cap = capability()
    governor.register_layer(layer())
    governor.register_capability(cap)

    ok = governor.lifecycle_manager.transition(cap, CapabilityLifecycleState.ACTIVE, "activation approved")
    bad = governor.lifecycle_manager.transition(cap, CapabilityLifecycleState.UNREGISTERED, "invalid jump")

    assert ok is True
    assert bad is False
    assert cap.lifecycle_state == CapabilityLifecycleState.ACTIVE


def test_registration_failures_report_observability_metrics():
    governor = CapabilityGovernor()
    governor.register_layer(LayerDescriptor(layer_id="", layer_name=""))
    governor.register_capability(capability(outputs=()))

    report = governor.build_report()

    assert report["registration_failures"] >= 2
    assert report["observability_metrics"]["registration_failure_count"] >= 2
    assert report["observability_metrics"]["registered_capability_count"] == 0


def test_boot_sequence_integration_and_report_rendering():
    governor = CapabilityGovernor()
    boot_report = governor.boot([
        (layer("ObjectLayer", ("object_tracking",)), [capability("object_tracking", owner="ObjectLayer")]),
        (layer("SpatialLayer", ("spatial_reasoning",)), [capability("spatial_reasoning", owner="SpatialLayer", deps=("object_tracking",))]),
    ])
    rendered = governor.render_report()

    assert boot_report["CAPABILITY_ARCHITECTURE_REPORT"] is True
    assert boot_report["registered_layers"] == 2
    assert boot_report["registered_capabilities"] == 2
    assert boot_report["dependency_graph_status"] == "VALID"
    assert boot_report["governor_visibility_status"] == "COMPLETE"
    assert "CAPABILITY ARCHITECTURE REPORT" in rendered


def test_adaptive_execution_governor_uses_capability_visibility():
    governor = AdaptiveExecutionGovernor()
    layer_descriptor = layer("DiagnosticLayer", ("diagnostic_profiler",))
    contract = capability(
        "diagnostic_profiler",
        owner="DiagnosticLayer",
        policies=(ExecutionPolicyName.DIAGNOSTIC,),
        activation_type=ActivationType.DIAGNOSTIC_ONLY,
    )

    governor.register_capability_layer(layer_descriptor, [contract])

    assert governor.discover_capability("diagnostic_profiler") is not None
    assert governor.can_activate_capability("diagnostic_profiler") is False
    governor.set_policy(ExecutionPolicyName.DIAGNOSTIC)
    assert governor.can_activate_capability("diagnostic_profiler") is True
