from runtime.dependency.dependency_activation_bridge import DependencyActivationBridge
from runtime.dynamic_concepts.dynamic_concept_runtime import DynamicConceptRuntime
from runtime.dynamic_concepts.dynamic_simulation_engine import DynamicSimulationEngine
from runtime.dynamic_concepts.gravity_reasoning import GravityReasoning
from runtime.dynamic_concepts.path_reasoning import PathReasoning
from runtime.dynamic_concepts.propagation_reasoning import PropagationReasoning
from runtime.memory.dynamic_concept_memory import DynamicConceptMemory
from runtime.process.process_context_runtime import ProcessContextRuntime
from runtime.reasoning.reasoning_orchestrator import ReasoningOrchestrator


def test_gravity_reasoning_models_fall_until_boundary():
    input_grid = [[0], [2], [0]]
    output_grid = [[0], [0], [2]]

    models = GravityReasoning().reason(
        input_grid=input_grid,
        output_grid=output_grid,
        runtime_context={"detected_concepts": ["gravity"]},
    )
    simulation = DynamicSimulationEngine().simulate(
        models[0],
        input_grid=input_grid,
        output_grid=output_grid,
    )

    assert models[0]["support_relationships"]["unsupported_count"] == 1
    assert models[0]["fall_distance"] == 1
    assert models[0]["candidate_transformation"] == {
        "operation": "translate",
        "dx": 0,
        "dy": 1,
    }
    assert simulation["simulation_accuracy"] == 1.0


def test_path_reasoning_constructs_reachability_path():
    input_grid = [[2, 0, 0, 3]]
    output_grid = [[2, 2, 2, 3]]

    models = PathReasoning().reason(
        input_grid=input_grid,
        output_grid=output_grid,
        runtime_context={"detected_concepts": ["path_finding"]},
    )
    simulation = DynamicSimulationEngine().simulate(
        models[0],
        input_grid=input_grid,
        output_grid=output_grid,
    )

    assert models[0]["best_path"] == [(0, 0), (0, 1), (0, 2), (0, 3)]
    assert models[0]["candidate_transformation"]["operation"] == "construct_path"
    assert simulation["simulation_accuracy"] == 1.0
    assert simulation["prediction_gain"] > 0.0


def test_propagation_and_state_evolution_generate_transitions():
    input_grid = [
        [0, 0, 0],
        [0, 4, 0],
        [0, 0, 0],
    ]
    output_grid = [
        [0, 4, 0],
        [4, 4, 4],
        [0, 4, 0],
    ]

    propagation = PropagationReasoning().reason(
        input_grid=input_grid,
        output_grid=output_grid,
        runtime_context={"detected_concepts": ["propagation"]},
    )[0]
    report = DynamicConceptRuntime(memory=DynamicConceptMemory()).run(
        input_grid=input_grid,
        output_grid=output_grid,
        detected_concepts=["propagation", "state_evolution"],
    )

    assert propagation["propagation_depth"] == 1
    assert report["DYNAMIC_CONCEPT_REPORT"]["simulations_executed"] > 0
    assert report["state_transition_count"] > 0
    assert "propagation" in report["dynamic_concepts_detected"]
    assert "state_evolution" in report["dynamic_concepts_detected"]


def test_dynamic_concept_memory_reuses_successful_simulation():
    memory = DynamicConceptMemory()
    model = {
        "concept_family": "path_finding",
        "dynamic_concept": "path_finding",
        "state_transitions": ["select_start_goal", "construct_path"],
        "simulation_plan": {
            "type": "path",
            "path": [(0, 0), (0, 1), (0, 2), (0, 3)],
        },
        "confidence": 0.94,
    }
    memory.remember(
        model,
        {"simulation_accuracy": 1.0, "prediction_gain": 0.5},
        success=True,
    )

    report = DynamicConceptRuntime(memory=memory).run(
        input_grid=[[2, 0, 0, 3]],
        output_grid=[[2, 2, 2, 3]],
        detected_concepts=["path_finding"],
    )

    assert report["reuse_hits"] >= 1
    assert report["DYNAMIC_CONCEPT_REPORT"]["reuse_hits"] >= 1


def test_orchestrator_surfaces_dynamic_concept_report():
    dependency = DependencyActivationBridge().activate(
        detected_concepts=["path_finding", "route_completion"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )
    process = ProcessContextRuntime().run(
        input_grid=[[2, 0, 0, 3]],
        output_grid=[[2, 2, 2, 3]],
        detected_concepts=["path_finding", "route_completion"],
        dependency_activation_report=dependency,
    )

    assert process["process_context_count"] > 0

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
            "input_grid": [[2, 0, 0, 3]],
            "output_grid": [[2, 2, 2, 3]],
            "task_signature": {},
        }
    )

    dynamic_report = report["DYNAMIC_CONCEPT_REPORT"]

    assert dynamic_report["dynamic_concepts_detected"]
    assert dynamic_report["simulations_executed"] > 0
    assert report["dynamic_concept_count"] > 0
    assert report["path_reasoning_count"] > 0
    assert report["dynamic_simulation_time"] > 0.0
