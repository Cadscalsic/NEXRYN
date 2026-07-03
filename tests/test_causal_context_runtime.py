from runtime.causal.causal_context_runtime import CausalContextRuntime
from runtime.causal.causal_inference_engine import CausalInferenceEngine
from runtime.causal.causal_simulator import CausalSimulator
from runtime.dependency.dependency_activation_bridge import DependencyActivationBridge
from runtime.memory.causal_context_memory import CausalContextMemory
from runtime.process.process_context_runtime import ProcessContextRuntime
from runtime.reasoning.reasoning_orchestrator import ReasoningOrchestrator


def _path_process_bundle():
    dependency = DependencyActivationBridge().activate(
        detected_concepts=["path_finding", "bridge_creation"],
        selected_tools=["dependency_reasoning", "process_semantics"],
    )
    process = ProcessContextRuntime().run(
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
        dependency_activation_report=dependency,
    )
    return dependency, process


def test_causal_inference_engine_builds_path_and_bridge_causes():
    dependency, process = _path_process_bundle()

    report = CausalInferenceEngine().infer(
        process_context_report=process,
        dependency_activation_report=dependency,
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
    )

    families = set(report["causal_families_detected"])
    pairs = report["cause_effect_pairs"]

    assert "path_cause" in families
    assert "bridge_cause" in families
    assert {
        "cause": "source_and_target_must_be_reachable",
        "effect": "route_created",
    } in pairs
    assert {
        "cause": "connector_introduced",
        "effect": "components_become_connected",
    } in pairs


def test_causal_context_runtime_generates_validated_contexts():
    dependency, process = _path_process_bundle()

    report = CausalContextRuntime(memory=CausalContextMemory()).run(
        input_grid=[[1, 0, 0, 1]],
        output_grid=[[1, 1, 1, 1]],
        process_context_report=process,
        dependency_activation_report=dependency,
    )

    causal_report = report["CAUSAL_CONTEXT_REPORT"]

    assert causal_report["causal_context_count"] > 0
    assert causal_report["causal_confidence"] > 0.0
    assert causal_report["causal_validation_score"] >= 0.7
    assert causal_report["causal_simulation_accuracy"] > 0.0
    assert report["causal_success_rate"] > 0.0


def test_causal_simulator_predicts_gravity_fall_until_boundary():
    context = {
        "causal_family": "gravity_cause",
        "cause": "unsupported_object",
        "effect": "object_falls_until_support_or_boundary",
        "supporting_process": "gravity",
        "supporting_dependencies": ["object", "support", "fall"],
        "confidence": 0.95,
        "state_before": {"state": "unsupported"},
        "state_after": {"state": "rest_state"},
        "constraints": ["support_or_boundary_stops_fall"],
        "contradictions": [],
    }

    simulation = CausalSimulator().simulate(
        context,
        input_grid=[[0], [1], [0]],
        output_grid=[[0], [0], [1]],
    )
    validation = CausalSimulator().validate(context, simulation)

    assert simulation["grid_prediction_accuracy"] == 1.0
    assert simulation["causal_simulation_accuracy"] == 1.0
    assert validation["causal_context_validated"] is True


def test_causal_memory_reuses_successful_causal_context():
    memory = CausalContextMemory()
    memory.remember(
        {
            "causal_family": "path_cause",
            "cause": "source_and_target_must_be_reachable",
            "effect": "route_created",
            "supporting_process": "path_finding",
            "supporting_dependencies": ["goal", "reachability"],
            "confidence": 0.95,
            "state_before": {"state": "goal"},
            "state_after": {"state": "completion"},
            "constraints": ["dependency_relationship_supported"],
            "contradictions": [],
        },
        simulation_accuracy=1.0,
        success=True,
    )
    dependency, process = _path_process_bundle()

    report = CausalContextRuntime(memory=memory).run(
        process_context_report=process,
        dependency_activation_report=dependency,
    )

    assert report["causal_reuse_hits"] >= 1
    assert report["causal_reuse_rate"] > 0.0


def test_orchestrator_surfaces_causal_context_runtime_telemetry():
    report = ReasoningOrchestrator().run_orchestration_cycle(
        {
            "enabled_tools": [
                "dependency_reasoning",
                "process_semantics",
            ],
            "detected_concepts": [
                "path_finding",
                "bridge_creation",
            ],
            "tool_selection_report": {
                "enabled_tools": [
                    "dependency_reasoning",
                    "process_semantics",
                ],
            },
            "input_grid": [[1, 0, 0, 1]],
            "output_grid": [[1, 1, 1, 1]],
            "task_signature": {},
        }
    )

    assert report["CAUSAL_CONTEXT_REPORT"]["causal_context_count"] > 0
    assert report["causal_context_count"] > 0
    assert report["causal_context_depth"] > 0
    assert report["causal_success_rate"] > 0.0
    assert report["causal_simulation_time"] > 0.0
