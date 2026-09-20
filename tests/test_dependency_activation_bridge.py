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
    assert report["DEPENDENCY_GRAPH_REPORT"]["graphs_generated"] == 1
    assert report["dependency_node_count"] > 0
    assert report["dependency_edge_count"] > 0


def test_graph_builder_creates_typed_dependency_graph_for_gravity():
    report = DependencyGraphBuilder().build(["gravity"])
    graph = report["dependency_graph"]
    node_types = {node["node_family"] for node in graph["nodes"]}
    edge_types = {edge["edge_type"] for edge in graph["edges"]}
    labels = [node["label"] for node in graph["nodes"]]

    assert "unsupported_object" in labels
    assert "falling" in labels
    assert "collision" in labels
    assert "rest_state" in labels
    assert {"CONDITION", "CONSTRAINT", "STATE"}.issubset(node_types)
    assert {"requires", "causes"}.issubset(edge_types)
    assert report["graph_confidence"] > 0.0
    assert report["support_score"] > 0.0


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
    assert report["dependency_activation_state"] == "ACTIVATED"
    assert report["DEPENDENCY_EXECUTION_REPORT"]["executions_started"] == 1
    assert report["DEPENDENCY_EXECUTION_REPORT"]["chains_generated"] > 0
    assert report["dependency_execution_count"] == 1
    assert report["dependency_execution_success_rate"] == 1.0
    assert report["DEPENDENCY_GRAPH_REPORT"]["graphs_generated"] == 1
    assert report["dependency_graph_count"] > 0
    assert report["dependency_node_count"] > 0
    assert report["dependency_edge_count"] > 0
    assert report["dependency_graph_validation_score"] > 0.0
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


def test_mandatory_activation_concepts_execute_through_gateway():
    report = DependencyActivationBridge().activate(
        detected_concepts=[
            "gravity",
            "falling",
            "support",
            "collision",
            "path_finding",
            "route_completion",
            "bridge_creation",
            "component_connection",
            "transformation_sequence",
            "multi_step_reasoning",
        ],
        selected_tools=[
            "dependency_reasoning",
            "process_semantics",
            "causal_reasoning",
        ],
    )

    execution = report["DEPENDENCY_EXECUTION_REPORT"]
    chains = {
        item["concept"]: item["resolved_dependency_chain"]
        for item in report["dependency_reports"]
    }

    assert report["dependency_activation_state"] == "ACTIVATED"
    assert execution["executions_started"] == 1
    assert execution["executions_completed"] == 1
    assert execution["chains_generated"] == 10
    assert report["dependency_chains_executed"] == 10
    assert report["dependency_execution_count"] == 1
    assert report["dependency_runtime_utilization"] == 1.0
    assert chains["gravity"] == [
        "gravity",
        "unsupported_object",
        "fall",
        "rest_state",
    ]
    assert chains["path_finding"] == [
        "path_finding",
        "start",
        "reachable_nodes",
        "goal",
    ]
    assert chains["bridge_creation"] == [
        "bridge_creation",
        "component_A",
        "connector",
        "component_B",
    ]
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
    assert report["DEPENDENCY_GRAPH_REPORT"]["graphs_generated"] == 1
    assert report["dependency_graph_count"] > 0
    assert report["dependency_node_count"] > 0
    assert report["dependency_edge_count"] > 0


def test_selected_dependency_reasoning_generates_audit_and_request():
    report = DependencyActivationBridge().activate(
        detected_concepts=[],
        selected_tools=["dependency_reasoning"],
        runtime_context={
            "enabled_tools": ["dependency_reasoning", "process_semantics"],
            "tool_selection_report": {
                "enabled_tools": ["dependency_reasoning", "process_semantics"],
            },
            "cognitive_budget_report": {
                "process_semantics_enabled": True,
                "dependency_reasoning_enabled": True,
            },
        },
    )

    audit = report["DEPENDENCY_ACTIVATION_AUDIT_REPORT"]
    failure = report["DEPENDENCY_ACTIVATION_FAILURE_REPORT"]

    assert audit["selected_tools"] == ["dependency_reasoning"]
    assert audit["activation_request_generated"] is True
    assert audit["selection_checkpoint"] == "request_created"
    assert audit["process_semantics_enabled"] is True
    assert audit["dependency_reasoning_enabled"] is True
    assert audit["activation_request_count"] == 1
    assert audit["dependency_activation_state"] == "REQUESTED"
    assert report["dependency_activation_state"] == "REQUESTED"
    assert report["dependency_execution_count"] == 1
    assert report["dependency_runtime_triggered"] is True
    assert report["DEPENDENCY_EXECUTION_REPORT"]["executions_started"] == 1
    assert failure["failure_detected"] is False
    assert report["activation_failures"] == []
