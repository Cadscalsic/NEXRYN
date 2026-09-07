from copy import deepcopy

from runtime.execution import ExecutableIntelligenceEngine, ExecutionFeedbackEngine, ExecutionMemory
from runtime.security import LearnedObjectExecutionGrantAuthority
from tests.test_e4_phase2_production_executor_grant_consumption import (
    LEARNED_OBJECT_ID,
    _arena,
    _budget,
    _candidate,
    _grant,
    _qualification,
    _validation,
)


def _production_result(tmp_path):
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()
    grant = _grant(
        engine=engine,
        candidate=candidate,
        run_id="run_phase3",
        budget=_budget(run_id="run_phase3"),
    )
    result = engine.run(
        semantic_intent="replace_color",
        operation="replace_color",
        input_grid=[[1, 1], [0, 0]],
        predicted_output=[[2, 2], [0, 0]],
        target_grid=[[2, 2], [0, 0]],
        validated_candidate=candidate,
        arena_execution_recommendation=_arena(candidate),
        candidate_qualification=_qualification(),
        execution_grant=grant,
        budget_admission=_budget(run_id="run_phase3"),
        governance_context={},
        execution_context={
            "run_id": "run_phase3",
            "outcome_feedback_storage_root": str(tmp_path),
        },
    )
    return result


def test_lawful_production_outcome_enters_feedback_lifecycle_with_retrieval(tmp_path):
    result = _production_result(tmp_path)
    production = result["PRODUCTION_EXECUTION_RESULT"]
    feedback = result["PRODUCTION_OUTCOME_FEEDBACK_REPORT"]

    assert production["execution_state"] == "PRODUCTION_EXECUTED"
    assert feedback["feedback_state"] == "PRODUCTION_OUTCOME_FEEDBACK_RECORDED"
    assert feedback["feedback_level"] == "F4"
    assert feedback["outcome_identity_contract"]["identity_complete"] is True
    assert feedback["outcome_evaluation"]["outcome_class"] == "SUCCESS"
    assert feedback["evidence_candidate"]["accepted_evidence_state"] == "NOT_ACCEPTED"
    assert feedback["accepted_evidence"]["accepted_evidence_state"] == (
        "NOT_ACCEPTED_BY_OUTCOME_FEEDBACK"
    )
    assert feedback["experience_record"]["learned_object_id"] == LEARNED_OBJECT_ID
    assert feedback["experience_record"]["execution_authority"] == "NONE"
    assert feedback["performance_history"]["execution_count"] == 1
    assert feedback["performance_history"]["success_count"] == 1
    assert feedback["future_retrieval"]["future_retrieval_state"] == (
        "PRIOR_OUTCOME_HISTORY_RETRIEVABLE"
    )
    assert feedback["successful_outcome_grants_future_execution"] is False
    assert feedback["reusable_execution_authority"] is False
    assert result["EXECUTABLE_INTELLIGENCE_REPORT"][
        "production_outcome_feedback_level"
    ] == "F4"


def test_outcome_feedback_is_idempotent_and_altered_receipts_fail_closed(tmp_path):
    production = _production_result(tmp_path)["PRODUCTION_EXECUTION_RESULT"]
    engine = ExecutionFeedbackEngine()

    first = engine.process_production_outcome(
        production,
        storage_root=tmp_path,
        current_run_id="run_phase3",
    )
    second = engine.process_production_outcome(
        production,
        storage_root=tmp_path,
        current_run_id="run_phase3",
    )
    copied = engine.process_production_outcome(
        deepcopy(production),
        storage_root=tmp_path,
        current_run_id="run_phase3",
    )
    altered = deepcopy(production)
    altered["execution_receipt"]["candidate_id"] = "altered_candidate"
    historical = engine.process_production_outcome(
        production,
        storage_root=tmp_path,
        current_run_id="future_run",
    )
    altered_result = engine.process_production_outcome(
        altered,
        storage_root=tmp_path,
        current_run_id="run_phase3",
    )

    assert first["persistence"]["idempotent_replay"] is True
    assert second["persistence"]["idempotent_replay"] is True
    assert copied["persistence"]["idempotent_replay"] is True
    assert altered_result["feedback_state"] == "PRODUCTION_OUTCOME_FEEDBACK_BLOCKED"
    assert altered_result["denial_reason"] == "EXECUTION_RECEIPT_ID_MISMATCH"
    assert historical["feedback_state"] == "PRODUCTION_OUTCOME_FEEDBACK_BLOCKED"
    assert historical["denial_reason"] == "HISTORICAL_RECEIPT_NEW_RUN_REPLAY"


def test_success_evidence_experience_and_history_cannot_execute_future_run(tmp_path):
    production = _production_result(tmp_path)["PRODUCTION_EXECUTION_RESULT"]
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        production,
        storage_root=tmp_path,
        current_run_id="run_phase3",
    )
    candidate = _candidate()
    authority_substitutes = [
        production,
        production["execution_receipt"],
        feedback["experience_record"],
        feedback["evidence_candidate"],
        feedback["performance_history"],
    ]

    for substitute in authority_substitutes:
        engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
        attempt = engine.execute_production(
            candidate=candidate,
            compiled_program={
                "steps": [
                    {
                        "operation": "replace_color",
                        "parameters": {"color_mapping": {1: 2}},
                    }
                ]
            },
            validation=_validation(),
            qualification=_qualification(),
            arena_selection=_arena(candidate),
            execution_grant=substitute,
            budget_admission=_budget(run_id="future_run"),
            governance_state={},
            execution_context={
                "run_id": "future_run",
                "production_execution_requested": True,
            },
            input_grid=[[1]],
            requested_operation="replace_color",
        )

        assert attempt["real_execution_performed"] is False
        assert attempt["underlying_executor_called"] is False


def test_failure_feedback_records_learning_input_without_punishment_policy(tmp_path):
    production = _production_result(tmp_path)["PRODUCTION_EXECUTION_RESULT"]
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        production,
        storage_root=tmp_path / "failure_feedback",
        current_run_id="run_phase3",
        evaluation_result={"outcome_class": "FAILURE", "failure_reason": "bad_result"},
    )

    assert feedback["feedback_state"] == "PRODUCTION_OUTCOME_FEEDBACK_RECORDED"
    assert feedback["outcome_evaluation"]["outcome_class"] == "FAILURE"
    assert feedback["performance_history"]["failure_count"] == 1
    assert feedback["performance_history"]["execution_authority"] == "NONE"
    assert feedback["experience_record"]["reusable_execution_authority"] is False
    assert feedback["authority"]["execution"] == "NONE"


def test_real_object_without_production_execution_has_no_feedback_event(tmp_path):
    real_id = "program-6097823aa7c9afc0"
    candidate = _candidate(
        candidate_id="adaptive_reuse:0",
        learned_object_id=real_id,
        source_learned_object_id=real_id,
    )
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    result = engine.execute_production(
        candidate=candidate,
        compiled_program={"steps": [{"operation": "replace_color", "parameters": {}}]},
        validation=_validation(),
        qualification={},
        arena_selection={
            "selection_state": "NO_SAFE_WINNER",
            "validation_probe_candidate": candidate,
            "validation_probe_authority": "SANDBOX_VALIDATION_ONLY",
        },
        execution_grant=None,
        budget_admission=None,
        governance_state={},
        execution_context={"run_id": "run_real_object", "production_execution_requested": True},
        input_grid=[[1]],
        requested_operation="replace_color",
    )
    feedback = ExecutionFeedbackEngine().process_production_outcome(
        result,
        storage_root=tmp_path,
        current_run_id="run_real_object",
    )

    assert result["real_execution_performed"] is False
    assert feedback["feedback_state"] == "PRODUCTION_OUTCOME_FEEDBACK_BLOCKED"
    assert feedback["denial_reason"] == "NO_PRODUCTION_OUTCOME"
