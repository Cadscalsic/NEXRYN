from runtime.dependency.dependency_activation_manager import (
    DEPENDENCY_NOT_REQUIRED,
    DEPENDENCY_REQUIRED,
    DependencyActivationManager,
)


def test_activation_manager_requires_dependency_for_structural_process_signal():
    manager = DependencyActivationManager()

    decision = manager.evaluate(
        {
            "process_note": "multi-step causal transformation sequence",
        },
        links_loaded=56,
    )

    assert decision["activation_state"] == DEPENDENCY_REQUIRED
    assert decision["dependency_required"] is True
    assert "causal" in decision["matched_signals"]


def test_activation_manager_promotes_runtime_request():
    manager = DependencyActivationManager()
    context = {"enabled_tools": []}
    decision = manager.evaluate(
        {"process_note": "hierarchical state transition"},
        links_loaded=2,
    )

    promoted = manager.promote_request(context, decision)

    request = promoted["runtime_tool_requests"]["dependency_reasoning"]
    assert request["request_state"] == "REQUESTED"
    assert "dependency_reasoning" in promoted["enabled_tools"]


def test_activation_manager_treats_enabled_dependency_tool_as_required():
    decision = DependencyActivationManager().evaluate(
        {
            "enabled_tools": ["dependency_reasoning"],
            "task_id": "arc_concept_gravity_simulation_15.json",
        },
        links_loaded=56,
    )

    assert decision["activation_state"] == DEPENDENCY_REQUIRED
    assert decision["dependency_required"] is True
    assert "gravity" in decision["matched_signals"]


def test_activation_manager_skips_when_no_links_or_triggers():
    decision = DependencyActivationManager().evaluate({}, links_loaded=0)

    assert decision["activation_state"] == DEPENDENCY_NOT_REQUIRED
    assert decision["dependency_required"] is False
