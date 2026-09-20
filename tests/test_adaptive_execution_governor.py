from runtime.resource_governance import (
    AdaptiveExecutionGovernor,
    ExecutionPolicyName,
    LayerExecutionCategory,
    LayerState,
)


def test_governor_registers_layers_and_exposes_metadata():
    governor = AdaptiveExecutionGovernor(register_defaults=False)

    governor.register_layer(
        "semantic_memory",
        description="Semantic memory access",
        dependencies=["knowledge_fabric"],
        owner="memory",
        default_state=LayerState.ON_DEMAND,
        execution_category=LayerExecutionCategory.COGNITIVE_MEMORY,
    )

    assert governor.get_layer_state("semantic_memory") == LayerState.ON_DEMAND
    assert governor.layer_metadata("semantic_memory")["owner"] == "memory"
    assert governor.layer_metadata("semantic_memory")["dependencies"] == [
        "knowledge_fabric"
    ]


def test_governor_is_execution_authority_for_layer_permissions():
    governor = AdaptiveExecutionGovernor(register_defaults=False)
    governor.register_layer("semantic_memory")
    governor.register_layer("knowledge_fabric")

    governor.activate_layer("semantic_memory")
    governor.defer_layer("knowledge_fabric")

    assert governor.can_execute("semantic_memory") is True
    assert governor.can_execute("knowledge_fabric") is False
    assert governor.can_execute("missing_layer") is False


def test_execution_plan_tracks_canonical_layer_state_sets():
    governor = AdaptiveExecutionGovernor(register_defaults=False)
    governor.register_layer("semantic_memory")
    governor.register_layer("knowledge_fabric")
    governor.register_layer("report_binding")

    governor.require_layer("semantic_memory")
    governor.defer_layer("knowledge_fabric")
    governor.block_layer("report_binding")

    plan = governor.create_execution_plan()

    assert plan.required_layers == {"semantic_memory"}
    assert plan.deferred_layers == {"knowledge_fabric"}
    assert plan.blocked_layers == {"report_binding"}


def test_execution_decisions_record_policy_and_transition_reason():
    governor = AdaptiveExecutionGovernor(
        execution_policy=ExecutionPolicyName.BALANCED,
        register_defaults=False,
    )
    governor.register_layer(
        "semantic_compilation",
        default_state=LayerState.ON_DEMAND,
    )

    governor.activate_layer(
        "semantic_compilation",
        reason="execution_transition_requested",
    )

    decision = governor.execution_decisions[-1].as_dict()
    assert decision["layer_name"] == "semantic_compilation"
    assert decision["previous_state"] == "ON_DEMAND"
    assert decision["new_state"] == "ACTIVE"
    assert decision["execution_policy"] == "BALANCED"
    assert decision["reason"] == "execution_transition_requested"


def test_governor_report_is_lightweight_and_operational():
    governor = AdaptiveExecutionGovernor(register_defaults=False)
    governor.register_layer("semantic_memory")
    governor.register_layer("knowledge_fabric")
    governor.activate_layer("semantic_memory")
    governor.defer_layer("knowledge_fabric")

    report = governor.build_report()
    rendered = governor.render_report()

    assert report["ADAPTIVE_EXECUTION_GOVERNOR_REPORT"] is True
    assert report["execution_policy"] == "BALANCED"
    assert report["registered_layers"] == 2
    assert report["active_layers"] == 1
    assert report["deferred_layers"] == 1
    assert report["governor_status"] == "OPERATIONAL"
    assert "ADAPTIVE EXECUTION GOVERNOR REPORT" in rendered
