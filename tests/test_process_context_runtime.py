from runtime.dependency.dependency_activation_bridge import DependencyActivationBridge
from runtime.memory.process_context_memory import ProcessContextMemory
from runtime.process.process_context_registry import ProcessContextRegistry
from runtime.process.process_context_runtime import ProcessContextRuntime
from runtime.process.process_simulator import ProcessSimulator
from runtime.process.state_transition_engine import StateTransitionEngine
from runtime.reasoning.reasoning_orchestrator import ReasoningOrchestrator


def test_state_transition_engine_infers_path_and_bridge_transitions():
    report = StateTransitionEngine().infer(
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
        concepts=["path_finding", "bridge_creation"],
    )

    transition_types = {
        transition["transition_type"]
        for transition in report["transitions"]
    }

    assert "object_added" in transition_types
    assert "path_constructed" in transition_types
    assert "bridge_created" in transition_types
    assert report["state_count"] > 0
    assert report["transition_count"] > 0


def test_process_context_runtime_models_path_finding_as_process():
    dependency_report = DependencyActivationBridge().activate(
        detected_concepts=["path_finding", "route_completion"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )

    report = ProcessContextRuntime(
        memory=ProcessContextMemory(),
        registry=ProcessContextRegistry(),
    ).run(
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
        dependency_activation_report=dependency_report,
    )

    process_report = report["PROCESS_CONTEXT_REPORT"]
    selected = report["selected_process_context"]

    assert process_report["process_contexts_generated"] > 0
    assert "path_finding" in process_report["process_families_detected"]
    assert selected["initial_state"]
    assert selected["final_state"]
    assert selected["transition_sequence"]
    assert report["process_context_count"] > 0
    assert report["state_transition_count"] > 0
    assert report["promotion_status"] == "PROCESS_CONTEXT_PROMOTED"


def test_process_simulator_scores_transition_and_dependency_consistency():
    model = {
        "context_name": "path_finding_runtime_context",
        "process_family": "path_finding",
        "initial_state": {"state_name": "goal"},
        "intermediate_states": [{"state_name": "reachability"}],
        "final_state": {"state_name": "completion"},
        "transition_sequence": [
            "goal->reachability",
            "reachability->completion",
        ],
        "dependencies": ["goal", "reachability", "completion"],
        "transition_events": [
            {
                "transition_type": "dependency_step",
                "transition": "goal->reachability",
                "confidence": 0.9,
                "evidence": {},
            }
        ],
    }

    simulation = ProcessSimulator().simulate(model)
    validation = ProcessSimulator().validate(model, simulation)

    assert simulation["transition_consistency"] > 0.0
    assert simulation["dependency_consistency"] > 0.0
    assert validation["process_validated"] is True


def test_process_context_memory_reuses_successful_process_model():
    memory = ProcessContextMemory()
    memory.remember(
        {
            "context_name": "path_finding_runtime_context",
            "process_family": "path_finding",
            "initial_state": {"state_name": "goal"},
            "intermediate_states": [{"state_name": "reachability"}],
            "final_state": {"state_name": "completion"},
            "transition_sequence": ["goal->reachability"],
            "dependencies": ["goal", "reachability"],
            "constraints": [],
            "expected_outcomes": ["path_finding_completed"],
            "confidence": 0.95,
            "concept": "path_finding",
            "transition_events": [],
            "state_count": 3,
            "process_depth": 1,
        },
        simulation_accuracy=1.0,
        success=True,
    )

    dependency_report = DependencyActivationBridge().activate(
        detected_concepts=["path_finding"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )
    report = ProcessContextRuntime(
        memory=memory,
        registry=ProcessContextRegistry(),
    ).run(
        dependency_activation_report=dependency_report,
    )

    assert report["reuse_hits"] >= 1
    assert report["process_reuse_rate"] > 0.0


def test_process_context_registry_tracks_lifecycle_metrics():
    registry = ProcessContextRegistry()
    runtime = ProcessContextRuntime(
        memory=ProcessContextMemory(),
        registry=registry,
    )
    dependency_report = DependencyActivationBridge().activate(
        detected_concepts=["bridge_creation"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )

    report = runtime.run(
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
        dependency_activation_report=dependency_report,
    )
    context_name = report["selected_process_context"]["context_name"]
    lifecycle = registry.record_usage(
        context_name,
        accuracy=report["simulation_accuracy"],
        reused=True,
    )

    assert lifecycle["usage_frequency"] >= 2
    assert lifecycle["reuse_frequency"] == 1
    assert lifecycle["success_rate"] > 0.0
    assert registry.report()["process_evolution"][context_name]


def test_orchestrator_surfaces_process_context_runtime_report():
    report = ReasoningOrchestrator().run_orchestration_cycle(
        {
            "enabled_tools": ["dependency_reasoning", "process_semantics"],
            "detected_concepts": ["path_finding", "route_completion"],
            "tool_selection_report": {
                "enabled_tools": ["dependency_reasoning", "process_semantics"],
            },
            "input_grid": [[1, 0, 0, 1]],
            "output_grid": [[1, 1, 1, 1]],
            "task_signature": {},
        }
    )

    assert report["PROCESS_CONTEXT_REPORT"]["process_contexts_generated"] > 0
    assert report["process_context_depth"] > 0
    assert report["process_context_confidence"] > 0.0
    assert report["state_transition_count"] > 0
    assert report["process_success_rate"] > 0.0
