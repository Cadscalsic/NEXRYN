from copy import deepcopy

from runtime.adaptive_reuse.program_reuse_engine import ProgramReuseEngine
from runtime.execution import ExecutableIntelligenceEngine, ExecutionFeedbackEngine, ExecutionMemory
from tests.test_e4_phase2_production_executor_grant_consumption import (
    _arena,
    _budget,
    _candidate,
    _grant,
    _qualification,
    _validation,
)
from tests.test_e5_phase2_real_runtime_learning_causality import (
    _EmptyMemory,
    _persist_experience,
    _real_runtime_engine,
    _source_experience,
)
from tests.test_e5_phase3_real_quality_efficiency_qualification import (
    _candidate_from_reuse,
    _execute_reuse_candidate,
    _quality_vector,
)


def _runtime_context_for(target_color):
    return {
        "concept": "replace_color",
        "winner_hypothesis": {
            "type": "replace_color",
            "operation": "replace_color",
        },
        "semantic_graph": {
            "concept_nodes": [{"concept": "replace_color"}],
        },
        "execution_plan": {
            "nodes": [{"operation": "replace_color"}],
        },
        "task_signature": f"replace_color_1_to_{target_color}",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "semantic_drift": 0.0,
        "effective_contradiction": 0.0,
        "context_compatibility": 1.0,
        "dependency_compatibility": 1.0,
        "world_model_compatibility": 1.0,
        "truth_integrity_preserved": True,
    }


def test_e5_r1_preserves_original_executable_parameters_across_reuse_path(tmp_path):
    source_run, feedback, experience = _source_experience(tmp_path / "source")
    production = source_run["PRODUCTION_EXECUTION_RESULT"]

    assert production["executable_payload"]["steps"][0]["parameters"] == {
        "color_mapping": {1: 2}
    }
    assert production["executable_payload"]["steps"][0]["parameter_provenance"] == {
        "color_mapping": "ORIGINAL_EXECUTION"
    }
    assert feedback["experience_record"]["program"]["steps"][0]["parameters"] == {
        "color_mapping": {1: 2}
    }
    assert experience["winner_hypothesis"]["parameters"] == {"color_mapping": {1: 2}}

    _persist_experience(tmp_path / "treatment", experience)
    reuse_report = _real_runtime_engine(tmp_path / "treatment").evaluate_reuse(
        _runtime_context_for(2)
    )
    composed = reuse_report["experience_reuse_report"]["composed_program"]
    step = composed["program_steps"][0]

    assert step["operation"] == "replace_color"
    assert step["parameters"] == {"color_mapping": {"1": 2}}
    assert step["parameter_provenance"] == {"color_mapping": "ORIGINAL_EXECUTION"}

    candidate = _candidate_from_reuse(reuse_report, "e5_r1_positive")
    result = _execute_reuse_candidate(candidate, "e5_r1_positive")

    assert result["real_execution_performed"] is True
    assert result["result"]["output_grid"] == [[2]]
    assert _quality_vector(result)["exact_success"] is True
    assert experience["execution_authority"] == "NONE"


def test_e5_r1_operation_only_replace_color_fails_closed():
    strategy = {
        "type": "replace_color",
        "operation": "replace_color",
        "confidence": 1.0,
    }

    report = ProgramReuseEngine(_EmptyMemory()).retrieve(_runtime_context_for(2), [strategy])

    assert report["program_reuse_success"] is False
    assert report["program_hits"] == 0
    assert report["composed_program"]["composition_state"] == "NO_PROGRAM_REUSE"


def test_e5_r1_parameter_conflict_does_not_blindly_claim_success(tmp_path):
    _, _, experience = _source_experience(tmp_path / "source")
    _persist_experience(tmp_path / "conflict", experience)
    reuse_report = _real_runtime_engine(tmp_path / "conflict").evaluate_reuse(
        _runtime_context_for(3)
    )
    candidate = _candidate_from_reuse(reuse_report, "e5_r1_conflict")
    result = _execute_reuse_candidate(candidate, "e5_r1_conflict")
    quality_against_conflict = {
        "exact_success": result["result"]["output_grid"] == [[3]],
        "output_grid": result["result"]["output_grid"],
        "expected": [[3]],
    }

    assert result["real_execution_performed"] is True
    assert quality_against_conflict["output_grid"] == [[2]]
    assert quality_against_conflict["exact_success"] is False


def test_e5_r1_null_and_failure_records_do_not_gain_authority(tmp_path):
    _, _, experience = _source_experience(tmp_path / "source")
    null_experience = deepcopy(experience)
    null_experience["experience_id"] = "e5_r1_null_translate_experience"
    null_experience["winner_hypothesis"]["type"] = "translate"
    null_experience["winner_hypothesis"]["operation"] = "translate"
    null_experience["winner_hypothesis"]["parameters"] = {"vector": [1, 0]}
    null_experience["semantic_graph"]["concept_nodes"] = [{"concept": "translate"}]
    null_experience["execution_plan"]["nodes"] = [{"operation": "translate"}]
    null_experience["program"]["steps"] = [
        {
            "operation": "translate",
            "parameters": {"vector": [1, 0]},
            "parameter_provenance": {"vector": "ORIGINAL_EXECUTION"},
        }
    ]
    null_experience["winner_hypothesis"]["executable_payload"] = {
        "operation": "translate",
        "steps": [
            {
                "operation": "translate",
                "parameters": {"vector": [1, 0]},
                "parameter_provenance": {"vector": "ORIGINAL_EXECUTION"},
            }
        ],
        "execution_authority": "NONE",
        "reusable_execution_authority": False,
    }
    _persist_experience(tmp_path / "null", null_experience)

    null_report = _real_runtime_engine(tmp_path / "null").evaluate_reuse(
        _runtime_context_for(2)
    )
    null_step = null_report["experience_reuse_report"]["composed_program"][
        "program_steps"
    ][0]

    assert null_step["operation"] == "translate"
    assert null_step["parameters"] == {"vector": [1, 0]}
    assert null_experience["execution_authority"] == "NONE"

    source_engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()
    grant = _grant(
        engine=source_engine,
        candidate=candidate,
        run_id="e5_r1_failure_source",
        budget=_budget(run_id="e5_r1_failure_source"),
    )
    source_run = source_engine.run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[[1]],
        predicted_output=[[2]],
        target_grid=[[2]],
        validated_candidate=candidate,
        arena_execution_recommendation=_arena(candidate),
        candidate_qualification=_qualification(),
        execution_grant=grant,
        budget_admission=_budget(run_id="e5_r1_failure_source"),
        governance_context={},
        execution_context={"run_id": "e5_r1_failure_source"},
    )
    failure = ExecutionFeedbackEngine().process_production_outcome(
        source_run["PRODUCTION_EXECUTION_RESULT"],
        storage_root=tmp_path / "failure_source",
        current_run_id="e5_r1_failure_source",
        evaluation_result={"outcome_class": "FAILURE"},
    )["experience_record"]

    assert failure["program"]["steps"][0]["parameters"] == {"color_mapping": {1: 2}}
    assert failure["evaluation_result"]["success"] is False
    assert failure["execution_authority"] == "NONE"
    assert failure["reusable_execution_authority"] is False
    assert failure["winner_hypothesis"]["execution_authority"] == "NONE"
