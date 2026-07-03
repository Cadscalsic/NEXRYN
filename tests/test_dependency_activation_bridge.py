from runtime.dependency.dependency_activation_bridge import DependencyActivationBridge
from runtime.dependency.dependency_graph_builder import DependencyGraphBuilder
from runtime.reasoning.reasoning_orchestrator import ReasoningOrchestrator


def test_graph_builder_creates_dependency_chain_for_path_finding():
    report = DependencyGraphBuilder().build(["path_finding"])

    assert report["dependency_chains"][0]["chain"] == [
        "goal",
        "reachability",
        "path_construction",
        "completion",
    ]
    assert report["dependency_depth"] > 0
    assert report["dependency_coverage"] == 1.0
    assert report["dependency_graph"]["edge_count"] > 0


def test_bridge_activates_dependency_and_process_runtime():
    report = DependencyActivationBridge().activate(
        detected_concepts=[
            "path_finding",
            "route_completion",
        ],
        selected_tools=[
            "dependency_reasoning",
            "process_semantics",
        ],
    )

    activation = report["DEPENDENCY_ACTIVATION_REPORT"]

    assert "dependency_reasoning" in activation["activated_tools"]
    assert "process_semantics" in activation["activated_tools"]
    assert report["dependency_chains_executed"] > 0
    assert report["dependency_chain_depth"] > 0
    assert report["dependency_chain_coverage"] > 0.0
    assert report["process_context_count"] > 0
    assert report["dependency_runtime_triggered"] is True
    assert activation["activation_failures"] == []


def test_bridge_generates_causal_context_for_gravity():
    report = DependencyActivationBridge().activate(
        detected_concepts=["gravity"],
        selected_tools=[
            "dependency_reasoning",
            "process_semantics",
            "causal_reasoning",
        ],
    )

    assert "causal_reasoning" in report["activated_tools"]
    assert report["dependency_chains_executed"] > 0
    assert report["process_context_count"] > 0
    assert report["causal_context_count"] > 0
    assert {
        context["state_transition"]
        for context in report["causal_contexts"]
    } >= {
        "support_removed->gravity_activated",
        "gravity_activated->object_falls",
    }


def test_bridge_emits_warning_when_required_tool_is_not_executable():
    report = DependencyActivationBridge().activate(
        detected_concepts=["path_finding"],
        selected_tools=[],
    )

    assert report["dependency_chains_executed"] > 0
    assert report["activation_failures"] == []


def test_orchestrator_surfaces_dependency_activation_telemetry():
    report = ReasoningOrchestrator().run_orchestration_cycle(
        {
            "enabled_tools": [
                "dependency_reasoning",
                "process_semantics",
            ],
            "detected_concepts": [
                "path_finding",
                "route_completion",
            ],
            "tool_selection_report": {
                "enabled_tools": [
                    "dependency_reasoning",
                    "process_semantics",
                ],
            },
            "task_signature": {},
        }
    )

    assert report["DEPENDENCY_ACTIVATION_REPORT"]["detected_concepts"]
    assert report["dependency_chains_executed"] > 0
    assert report["dependency_chain_depth"] > 0
    assert report["process_context_count"] > 0
    assert report["dependency_runtime_triggered"] is True
