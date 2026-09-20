from copy import deepcopy

from runtime.execution import ExecutableIntelligenceEngine, ExecutionMemory
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
    _runtime_context,
    _source_experience,
)


TARGET_GRID = [[2]]


def _candidate_from_reuse(report, run_id):
    composed = report["experience_reuse_report"].get("composed_program", {})
    steps = composed.get("program_steps", [])
    if not steps:
        return None
    return _candidate(
        candidate_id=f"reuse_candidate:{run_id}",
        canonical_provenance={
            "persisted_learned_object": True,
            "retrieval_state": "RETRIEVED",
            "retrieval_id": report["experience_reuse_report"]["reused_strategies"][0][
                "source_experience_id"
            ],
        },
        program={"steps": deepcopy(steps)},
    )


def _execute_reuse_candidate(candidate, run_id):
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
        input_grid=[[1]],
        requested_operation="replace_color",
    )


def _quality_vector(production):
    output_grid = (
        production.get("result", {}).get("output_grid")
        if isinstance(production, dict)
        else None
    )
    return {
        "production_executed": production.get("real_execution_performed") is True,
        "exact_success": output_grid == TARGET_GRID,
        "accuracy": 1.0 if output_grid == TARGET_GRID else 0.0,
        "final_score": 1.0 if output_grid == TARGET_GRID else 0.0,
        "validation_result": production.get("execution_state", "NOT_REACHED"),
        "residual_error": 0 if output_grid == TARGET_GRID else "UNAVAILABLE",
        "task_completion_state": (
            "EXACT_OUTPUT_MATCH"
            if output_grid == TARGET_GRID
            else "OUTPUT_MISMATCH"
            if output_grid is not None
            else "NOT_REACHED"
        ),
    }


def _cost_vector(reuse_report, production):
    behavior = _behavior_vector(reuse_report)
    nested = reuse_report["experience_reuse_report"]
    operation_calls = (
        production.get("result", {}).get("operation_call_count", 0)
        if isinstance(production, dict)
        else 0
    )
    return {
        "reuse_elapsed_seconds": nested.get("elapsed_seconds"),
        "reuse_attempts": nested.get("retrieval_attempts"),
        "candidate_attempts": behavior["candidate_count"],
        "repair_attempts": 0,
        "synthesis_attempts": len(behavior["synthesis_actions"]),
        "executor_invocations": operation_calls,
        "underlying_executor_called": (
            production.get("underlying_executor_called") is True
            if isinstance(production, dict)
            else False
        ),
        "realized_operation_units": (
            int(nested.get("retrieval_attempts", 0) or 0)
            + int(behavior["candidate_count"])
            + int(operation_calls or 0)
        ),
    }


def _run_condition(storage_root, run_id, experience=None):
    if experience:
        _persist_experience(storage_root, experience)
    reuse_report = _real_runtime_engine(storage_root).evaluate_reuse(_runtime_context())
    candidate = _candidate_from_reuse(reuse_report, run_id)
    production = (
        _execute_reuse_candidate(candidate, run_id)
        if candidate is not None
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
        "quality": _quality_vector(production),
        "cost": _cost_vector(reuse_report, production),
    }


def test_phase3_exact_match_reuse_restores_quality_but_not_efficiency(tmp_path):
    _, _, experience = _source_experience(tmp_path / "source")

    repeats = []
    for repeat in range(3):
        control = _run_condition(tmp_path / f"control_{repeat}", f"control:{repeat}")
        treatment = _run_condition(
            tmp_path / f"treatment_{repeat}",
            f"treatment:{repeat}",
            experience=experience,
        )
        removal = _run_condition(tmp_path / f"removal_{repeat}", f"removal:{repeat}")
        repeats.append((control, treatment, removal))

        assert control["behavior"]["selected_candidate"] == "NO_PROGRAM_REUSE"
        assert treatment["behavior"]["selected_candidate"] == "COMPOSED_FROM_EXPERIENCE"
        assert removal["behavior"] == control["behavior"]
        assert treatment["quality"]["exact_success"] is True
        assert treatment["quality"]["accuracy"] > control["quality"]["accuracy"]
        assert treatment["cost"]["realized_operation_units"] > control["cost"][
            "realized_operation_units"
        ]

    assert all(item[1]["behavior"] != item[0]["behavior"] for item in repeats)
    assert all(item[1]["quality"]["exact_success"] is True for item in repeats)


def test_phase3_null_and_warm_cache_do_not_prove_specific_improvement(tmp_path):
    _, _, experience = _source_experience(tmp_path / "source")
    unrelated = deepcopy(experience)
    unrelated["experience_id"] = "phase3_unrelated_translate_experience"
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
    unrelated["task_signature"] = "phase3_unrelated_translate_task"

    cold_control = _run_condition(tmp_path / "cold_control", "cold_control")
    warm_control = _run_condition(tmp_path / "warm_control", "warm_control")
    null = _run_condition(tmp_path / "null", "null", experience=unrelated)

    assert cold_control["behavior"] == warm_control["behavior"]
    assert cold_control["quality"] == warm_control["quality"]
    assert null["quality"]["exact_success"] is False
    assert null["behavior"]["execution_operation"] != "replace_color"
