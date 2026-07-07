from runtime.capabilities import CognitiveCapabilityOrchestrator
from runtime.reasoning.reasoning_orchestrator import ReasoningOrchestrator
from runtime.reasoning.transformation_synthesis_engine import TransformationSynthesisEngine


def test_capability_orchestrator_builds_composition_report():
    report = CognitiveCapabilityOrchestrator().build_report(
        runtime_context={
            "detected_concepts": ["color_mapping", "path_finding"],
            "truth_commitments": [{"truth_id": "palette_invariant"}],
        },
        reports={
            "color_mapping_report": {
                "mapping_confidence": 0.92,
                "program_accuracy": 1.0,
                "mapping_matrix": {
                    "mapping_type": "object_specific",
                    "mapping": {"1": 2},
                },
                "selected_program": {
                    "steps": [{
                        "operation": "recolor",
                        "parameters": {"mapping": {"1": 2}},
                    }],
                },
                "candidate_mappings": [{"mapping": {"1": 2}}],
                "validated_mappings": [{"mapping": {"1": 2}}],
            },
            "dependency_activation_report": {
                "dependency_chains_executed": 1,
                "dependency_chain_coverage": 0.9,
                "dependency_execution_success_rate": 1.0,
                "dependency_reports": [{"concept": "color_mapping"}],
            },
            "process_context_runtime_report": {
                "process_validation_score": 0.88,
                "process_context_confidence": 0.86,
                "process_success_rate": 1.0,
                "process_contexts": [{"context_name": "color_process"}],
            },
            "transformation_synthesis_report": {
                "transformation_confidence": 0.91,
                "transformation_accuracy": 1.0,
                "selected_program": {
                    "program_type": "transformation_program",
                    "steps": [{
                        "operation": "recolor",
                        "parameters": {"mapping": {"1": 2}},
                    }],
                },
                "candidate_count": 1,
            },
            "causal_context_runtime_report": {
                "causal_confidence": 0.86,
                "causal_validation_score": 0.9,
                "causal_success_rate": 1.0,
                "root_cause_candidates": ["palette_rule"],
                "causal_contexts": [{"cause": "palette_rule", "effect": "recolor"}],
            },
        },
    )

    assert report["COGNITIVE_CAPABILITY_REPORT"] is True
    assert "color_mapping" in report["capabilities_executed"]
    assert "program_synthesis" in report["capabilities_executed"]
    assert report["capability_confidence"]["color_mapping"] > 0.9
    assert report["cooperation_events"]
    assert report["shared_programs"]
    assert report["shared_dependencies"]
    assert report["shared_contexts"]
    assert report["shared_truths"]
    assert report["generated_hypotheses"]
    assert report["validated_hypotheses"]
    assert report["successful_programs"]
    assert "Executed" in report["reasoning_summary"]


def test_reasoning_orchestrator_surfaces_cognitive_capability_report():
    report = ReasoningOrchestrator().run_orchestration_cycle({
        "enabled_tools": ["dependency_reasoning", "process_semantics"],
        "detected_concepts": ["path_finding", "bridge_creation"],
        "tool_selection_report": {
            "enabled_tools": ["dependency_reasoning", "process_semantics"],
        },
        "input_grid": [[1, 0, 0, 1]],
        "output_grid": [[1, 1, 1, 1]],
        "task_signature": {},
    })

    capability = report["COGNITIVE_CAPABILITY_REPORT"]

    assert capability["COGNITIVE_CAPABILITY_REPORT"] is True
    assert capability["capabilities_executed"]
    assert capability["generated_hypotheses"]
    assert capability["cooperation_events"]
    assert report["capability_success_rate"] >= 0.0


def test_transformation_synthesis_generates_diagonal_reflection_candidate():
    report = TransformationSynthesisEngine().synthesize(
        input_grid=[
            [1, 0, 0],
            [2, 3, 0],
            [0, 4, 5],
        ],
        output_grid=[
            [1, 2, 0],
            [0, 3, 4],
            [0, 0, 5],
        ],
        detected_concepts=["reflection"],
    )

    kinds = {candidate["kind"] for candidate in report["ranked_candidates"]}

    assert "diagonal_reflection" in kinds
    assert report["selected_program"]["step_count"] > 0
