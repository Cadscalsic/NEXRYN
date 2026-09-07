from copy import deepcopy

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
    _behavior_vector,
    _persist_experience,
    _real_runtime_engine,
)
from tests.test_e5_phase3_real_quality_efficiency_qualification import (
    _candidate_from_reuse,
)


def _context(source_color, target_color):
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
        "task_signature": f"replace_color_{source_color}_to_{target_color}",
        "identity_runtime_state": "IDENTITY_RUNTIME_STABLE",
        "identity_runtime_ready": True,
        "semantic_drift": 0.0,
        "effective_contradiction": 0.0,
        "context_compatibility": 1.0,
        "dependency_compatibility": 1.0,
        "world_model_compatibility": 1.0,
        "truth_integrity_preserved": True,
    }


def _source_experience_for(storage_root, source_color, target_color):
    run_id = f"phase3b_source_{source_color}_to_{target_color}"
    candidate = _candidate(
        candidate_id=f"candidate:{run_id}",
        program={
            "steps": [
                {
                    "operation": "replace_color",
                    "parameters": {"color_mapping": {source_color: target_color}},
                }
            ]
        },
    )
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    grant = _grant(
        engine=engine,
        candidate=candidate,
        run_id=run_id,
        budget=_budget(run_id=run_id),
    )
    source_run = engine.run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[[source_color]],
        predicted_output=[[target_color]],
        target_grid=[[target_color]],
        validated_candidate=candidate,
        arena_execution_recommendation=_arena(candidate),
        candidate_qualification=_qualification(),
        execution_grant=grant,
        budget_admission=_budget(run_id=run_id),
        governance_context={},
        execution_context={"run_id": run_id},
    )
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        source_run["PRODUCTION_EXECUTION_RESULT"],
        storage_root=storage_root,
        current_run_id=run_id,
    )
    return source_run, feedback, feedback["experience_record"]


def _execute_candidate(candidate, run_id, input_value):
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    grant = _grant(
        engine=engine,
        candidate=candidate,
        run_id=run_id,
        budget=_budget(run_id=run_id),
    )
    return engine.execute_production(
        candidate=candidate,
        compiled_program=candidate["program"],
        validation=_validation(),
        qualification=_qualification(),
        arena_selection=_arena(candidate),
        execution_grant=grant,
        budget_admission=_budget(run_id=run_id),
        governance_state={},
        execution_context={"run_id": run_id, "production_execution_requested": True},
        input_grid=[[input_value]],
        requested_operation="replace_color",
    )


def _quality(production, expected):
    output = production.get("result", {}).get("output_grid")
    exact = output == [[expected]]
    return {
        "output_grid": output,
        "expected_output": [[expected]],
        "exact_success": exact,
        "accuracy": 1.0 if exact else 0.0,
        "final_score": 1.0 if exact else 0.0,
        "validation_result": production.get("execution_state", "NOT_REACHED"),
        "residual_error": 0 if exact else "UNAVAILABLE",
    }


def _cost(reuse_report, production):
    behavior = _behavior_vector(reuse_report)
    nested = reuse_report["experience_reuse_report"]
    executor_invocations = production.get("result", {}).get("operation_call_count", 0)
    return {
        "retrieval_attempts": nested.get("retrieval_attempts"),
        "candidate_attempts": behavior["candidate_count"],
        "synthesis_attempts": len(behavior["synthesis_actions"]),
        "repair_attempts": 0,
        "executor_invocations": executor_invocations,
        "realized_operation_units": (
            int(nested.get("retrieval_attempts", 0) or 0)
            + int(behavior["candidate_count"])
            + int(executor_invocations or 0)
        ),
        "wall_time": nested.get("elapsed_seconds"),
        "active_compute_time": nested.get("cpu_time", "UNAVAILABLE"),
        "routes_realized": "UNAVAILABLE",
        "depth_realized": "UNAVAILABLE",
    }


def _condition(storage_root, run_id, source_color, target_color, experience=None):
    if experience:
        _persist_experience(storage_root, experience)
    reuse_report = _real_runtime_engine(storage_root).evaluate_reuse(
        _context(source_color, target_color)
    )
    candidate = _candidate_from_reuse(reuse_report, run_id)
    production = (
        _execute_candidate(candidate, run_id, source_color)
        if candidate
        else {
            "execution_state": "NOT_REACHED",
            "real_execution_performed": False,
            "underlying_executor_called": False,
            "result": {},
        }
    )
    return {
        "reuse": reuse_report,
        "behavior": _behavior_vector(reuse_report),
        "production": production,
        "quality": _quality(production, target_color),
        "cost": _cost(reuse_report, production),
    }


def test_phase3b_multi_parameter_quality_signal_and_no_efficiency_promotion(tmp_path):
    cases = [(1, 2), (1, 3), (2, 4)]
    case_results = []

    for source_color, target_color in cases:
        _, feedback, experience = _source_experience_for(
            tmp_path / f"source_{source_color}_{target_color}",
            source_color,
            target_color,
        )
        assert feedback["feedback_level"] == "F4"
        assert experience["program"]["steps"][0]["parameters"] == {
            "color_mapping": {source_color: target_color}
        }

        for repeat in range(3):
            control = _condition(
                tmp_path / f"control_{source_color}_{target_color}_{repeat}",
                f"control:{source_color}:{target_color}:{repeat}",
                source_color,
                target_color,
            )
            treatment = _condition(
                tmp_path / f"treatment_{source_color}_{target_color}_{repeat}",
                f"treatment:{source_color}:{target_color}:{repeat}",
                source_color,
                target_color,
                experience=experience,
            )
            removal = _condition(
                tmp_path / f"removal_{source_color}_{target_color}_{repeat}",
                f"removal:{source_color}:{target_color}:{repeat}",
                source_color,
                target_color,
            )

            assert control["quality"]["exact_success"] is False
            assert treatment["quality"]["exact_success"] is True
            assert removal["quality"] == control["quality"]
            assert treatment["behavior"]["selected_candidate"] == "COMPOSED_FROM_EXPERIENCE"
            assert treatment["cost"]["realized_operation_units"] > control["cost"][
                "realized_operation_units"
            ]
            case_results.append((control, treatment, removal))

    assert len(case_results) == 9
    assert all(item[1]["quality"]["accuracy"] > item[0]["quality"]["accuracy"] for item in case_results)
    assert all(
        item[1]["cost"]["realized_operation_units"]
        > item[0]["cost"]["realized_operation_units"]
        for item in case_results
    )


def test_phase3b_conflict_null_and_warm_controls(tmp_path):
    _, _, experience = _source_experience_for(tmp_path / "source_1_2", 1, 2)

    conflict = _condition(
        tmp_path / "conflict",
        "conflict",
        1,
        3,
        experience=experience,
    )
    assert conflict["production"]["real_execution_performed"] is True
    assert conflict["quality"]["output_grid"] == [[2]]
    assert conflict["quality"]["exact_success"] is False

    unrelated = deepcopy(experience)
    unrelated["experience_id"] = "phase3b_translate_placebo"
    unrelated["winner_hypothesis"]["type"] = "translate"
    unrelated["winner_hypothesis"]["operation"] = "translate"
    unrelated["winner_hypothesis"]["parameters"] = {"vector": [1, 0]}
    unrelated["winner_hypothesis"]["executable_payload"] = {
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
    unrelated["semantic_graph"]["concept_nodes"] = [{"concept": "translate"}]
    unrelated["execution_plan"]["nodes"] = [{"operation": "translate"}]
    unrelated["program"]["steps"] = [
        {
            "operation": "translate",
            "parameters": {"vector": [1, 0]},
            "parameter_provenance": {"vector": "ORIGINAL_EXECUTION"},
        }
    ]
    unrelated["task_signature"] = "phase3b_translate_placebo"

    null = _condition(tmp_path / "null", "null", 1, 2, experience=unrelated)
    assert null["quality"]["exact_success"] is False
    assert null["behavior"]["execution_operation"] != "replace_color"

    cold = _condition(tmp_path / "cold", "cold", 1, 2)
    warm = _condition(tmp_path / "warm", "warm", 1, 2)
    assert warm["quality"] == cold["quality"]
    assert warm["behavior"] == cold["behavior"]
