from runtime.dependency.dependency_activation_bridge import DependencyActivationBridge
from runtime.memory.process_context_memory import ProcessContextMemory
from runtime.process.process_context_generator import ProcessContextGenerator
from runtime.process.process_context_registry import ProcessContextRegistry
from runtime.process.process_context_runtime import ProcessContextRuntime
from runtime.process.process_context_validator import ProcessContextValidator
from runtime.process.state_transition_builder import StateTransitionBuilder
from runtime.reasoning.reasoning_orchestrator import ReasoningOrchestrator


def test_state_transition_builder_extracts_gravity_state_flow():
    dependency = DependencyActivationBridge().activate(
        detected_concepts=["gravity"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )
    graph = dependency["dependency_graph_discovery_report"]["dependency_graph"]

    report = StateTransitionBuilder().build(graph, "gravity_process")
    names = [state["state_name"] for state in report["states"]]

    assert names[:4] == ["unsupported", "falling", "collision", "stable"]
    assert report["transition_count"] >= 3
    assert report["state_confidence"] > 0.0
    assert report["transition_confidence"] > 0.0


def test_process_context_generator_turns_dependency_graph_into_process():
    dependency = DependencyActivationBridge().activate(
        detected_concepts=["path_finding"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )

    report = ProcessContextGenerator(memory=ProcessContextMemory()).generate(
        dependency_graph_report=dependency["dependency_graph_discovery_report"],
    )
    generation = report["PROCESS_CONTEXT_GENERATION_REPORT"]
    selected = report["selected_process_context"]

    assert generation["process_contexts_generated"] > 0
    assert "path_process" in generation["process_families_detected"]
    assert generation["states_generated"] > 0
    assert generation["transitions_generated"] > 0
    assert generation["process_depth"] > 0
    assert generation["process_confidence"] > 0.0
    assert selected["initial_state"]
    assert selected["final_state"]
    assert selected["transition_sequence"]


def test_graph_extraction_empty_absent_and_none_discovery_terminates():
    generator = ProcessContextGenerator(memory=ProcessContextMemory())

    assert generator._graphs_from_report({}) == []
    assert generator._graphs_from_report(None) == []
    assert generator._graphs_from_report({"dependency_graph_discovery_report": {}}) == []


def test_graph_extraction_preserves_valid_direct_collection_and_nested_discovery():
    generator = ProcessContextGenerator(memory=ProcessContextMemory())
    graph_a = {"graph_id": "graph_a", "nodes": [{"id": "a"}], "edges": []}
    graph_b = {"graph_id": "graph_b", "nodes": [{"id": "b"}], "edges": []}

    assert generator._graphs_from_report({"dependency_graph": graph_a}) == [graph_a]
    assert generator._graphs_from_report({"dependency_graphs": [graph_a, graph_b]}) == [
        graph_a,
        graph_b,
    ]
    assert generator._graphs_from_report(
        {"dependency_graph_discovery_report": {"dependency_graph": graph_b}}
    ) == [graph_b]


def test_graph_extraction_cyclic_discovery_terminates_without_recursion_error():
    generator = ProcessContextGenerator(memory=ProcessContextMemory())
    cyclic = {}
    cyclic["dependency_graph_discovery_report"] = cyclic

    assert generator._graphs_from_report(cyclic) == []


def test_graph_extraction_excessive_acyclic_nesting_terminates_without_recursion_error():
    generator = ProcessContextGenerator(memory=ProcessContextMemory())
    report = {"dependency_graph": {"graph_id": "too_deep", "nodes": [], "edges": []}}
    for _ in range(80):
        report = {"dependency_graph_discovery_report": report}

    assert generator._graphs_from_report(report) == []


def test_process_context_validator_rejects_broken_generated_process():
    validation = ProcessContextValidator().validate_generated(
        {
            "initial_state": {},
            "intermediate_states": [],
            "final_state": {},
            "transition_sequence": [],
            "dependencies": [],
        },
        {},
        {},
    )

    assert validation["process_validated"] is False
    assert validation["validation_blockers"]
    assert validation["process_validation_score"] < 0.70


def test_process_context_generator_reuses_successful_process_memory():
    memory = ProcessContextMemory()
    dependency = DependencyActivationBridge().activate(
        detected_concepts=["bridge_creation"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )
    generator = ProcessContextGenerator(memory=memory)

    first = generator.generate(
        dependency_graph_report=dependency["dependency_graph_discovery_report"],
    )
    second = generator.generate(
        dependency_graph_report=dependency["dependency_graph_discovery_report"],
    )

    assert first["process_context_count"] > 0
    assert second["reuse_hits"] >= 1
    assert second["process_reuse_rate"] > 0.0
    assert memory.build_report()["transition_motif_count"] > 0
    assert memory.build_report()["state_evolution_pattern_count"] > 0


def test_process_context_runtime_surfaces_generation_telemetry():
    dependency = DependencyActivationBridge().activate(
        detected_concepts=["path_finding", "route_completion"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )
    report = ProcessContextRuntime(
        memory=ProcessContextMemory(),
        registry=ProcessContextRegistry(),
    ).run(dependency_activation_report=dependency)

    generation = report["PROCESS_CONTEXT_GENERATION_REPORT"]

    assert generation["process_contexts_generated"] > 0
    assert report["process_context_count"] > 0
    assert report["process_state_count"] > 0
    assert report["process_transition_count"] > 0
    assert report["process_depth"] > 0
    assert report["process_validation_score"] > 0.0
    assert report["process_generation_time"] >= 0.0


def test_orchestrator_surfaces_process_context_generation_report():
    report = ReasoningOrchestrator().run_orchestration_cycle(
        {
            "enabled_tools": ["dependency_reasoning", "process_semantics"],
            "detected_concepts": ["bridge_creation"],
            "tool_selection_report": {
                "enabled_tools": ["dependency_reasoning", "process_semantics"],
            },
            "task_signature": {},
        }
    )

    assert report["PROCESS_CONTEXT_GENERATION_REPORT"]["process_contexts_generated"] > 0
    assert report["process_state_count"] > 0
    assert report["process_transition_count"] > 0
    assert report["process_generation_time"] >= 0.0
