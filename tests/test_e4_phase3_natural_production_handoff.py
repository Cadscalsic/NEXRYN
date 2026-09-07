from copy import deepcopy

import pytest

from runtime.execution import ExecutableIntelligenceEngine, ExecutionMemory
from runtime.reporting import (
    CompactReportBuilder,
    DeterministicFinalReportRenderer,
    NaturalProductionHandoffObserver,
)
from runtime.security import LearnedObjectExecutionGrantAuthority


LEARNED_OBJECT_ID = "program-e4-phase3"


def _candidate(**overrides):
    data = {
        "candidate_id": "candidate-e4-natural",
        "source": "adaptive_reuse",
        "candidate_type": "PROGRAM",
        "learned_object_id": LEARNED_OBJECT_ID,
        "source_learned_object_id": LEARNED_OBJECT_ID,
        "source_program_id": LEARNED_OBJECT_ID,
        "run_id": "run-e4-phase3",
        "task_id": "task-e4-phase3",
        "producer_operation_id": "producer-op-1",
        "permitted_operations": ["replace_color"],
        "canonical_provenance": {"retrieval_state": "RETRIEVED"},
    }
    data.update(overrides)
    return data


def _validation(**overrides):
    data = {
        "validation_id": "validation-e4-phase3",
        "validation_state": "SANDBOX_VALIDATION_PASSED",
        "validation_success": True,
        "evidence_sufficient_for_execution_use": True,
        "evidence_acceptance_state": "ACCEPTED",
    }
    data.update(overrides)
    return data


def _qualification(**overrides):
    data = {
        "qualification_id": "qualification-e4-phase3",
        "qualification_state": "QUALIFIED",
        "governance_constraints_satisfied": True,
    }
    data.update(overrides)
    return data


def _arena(**overrides):
    candidate = overrides.pop("candidate", _candidate())
    data = {
        "arena_selection_id": "arena-e4-phase3",
        "selection_state": "WINNER_SELECTED",
        "selected_candidate_id": candidate["candidate_id"],
        "selected_candidate": candidate,
        "execution_mode": "real",
    }
    data.update(overrides)
    return data


def _budget(run_id="run-e4-phase3", **overrides):
    data = {
        "runtime_budget_state": "RUNTIME_BUDGET_FINALIZED",
        "route_budget_enforcement_state": "ROUTE_BUDGET_ADMITTED",
        "realized_overrun_state": "NO_REALIZED_OVERRUN",
        "violation_reason": "NONE",
        "run_id": run_id,
        "budget_admission_id": f"budget:{run_id}",
    }
    data.update(overrides)
    return data


def _grant(candidate=None, run_id="run-e4-phase3", budget=None):
    candidate = candidate or _candidate()
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    grant_candidate = deepcopy(candidate)
    grant_candidate["candidate_fingerprint"] = engine._candidate_fingerprint(
        candidate
    )
    return LearnedObjectExecutionGrantAuthority().issue_grant(
        run_id=run_id,
        candidate=grant_candidate,
        learned_object={
            "learned_object_id": LEARNED_OBJECT_ID,
            "canonical_provenance": {"retrieval_state": "RETRIEVED"},
        },
        arena_selection=_arena(candidate=candidate),
        validation=_validation(),
        qualification=_qualification(),
        execution_scope={"operation": "replace_color", "max_steps": 1},
        budget_admission=budget or _budget(run_id),
    )


def _trace(**overrides):
    values = {
        "run_id": "run-e4-phase3",
        "task_id": "task-e4-phase3",
        "candidate": _candidate(),
        "sandbox_validation": _validation(),
        "qualification": _qualification(),
        "arena_selection": _arena(),
        "execution_grant": None,
        "budget_admission": None,
        "production_execution": {},
        "run_budget_state": "RUNTIME_BUDGET_FINALIZED",
    }
    values.update(overrides)
    return NaturalProductionHandoffObserver().build_trace(**values)


def test_tie_requires_review_lawfully_blocks_grant_and_executor():
    trace = _trace(
        arena_selection=_arena(
            selection_state="TIE_REQUIRES_REVIEW",
            selected_candidate_id=None,
            selected_candidate={},
            execution_mode="review",
        )
    )

    assert trace["phase_3_state"] == "NATURAL_RUNTIME_LAWFULLY_BLOCKED_UPSTREAM"
    assert trace["first_blocked_boundary"] == "ARENA_TIE_REQUIRES_REVIEW"
    assert trace["grant_expected"] is False
    assert trace["candidate_budget_admission_expected"] is False
    assert trace["production_executor_expected"] is False
    assert trace["real_execution_performed"] is False
    assert trace["unauthorized_downstream_activity"] == "NONE"
    assert trace["reachability_gap"] is False


def test_no_safe_winner_lawfully_blocks_grant_and_production_execution():
    trace = _trace(
        arena_selection=_arena(
            selection_state="NO_SAFE_WINNER",
            selected_candidate_id=None,
            selected_candidate={},
            execution_mode="review",
        )
    )

    assert trace["first_blocked_boundary"] == "ARENA_NO_SAFE_WINNER"
    assert trace["grant_expected"] is False
    assert trace["real_execution_performed"] is False
    assert trace["boundary_states"]["execution_grant"] == "NOT_REACHED"


def test_safe_winner_without_grant_is_a_natural_handoff_gap():
    trace = _trace()

    assert trace["grant_expected"] is True
    assert trace["phase_3_state"] == "NATURAL_HANDOFF_GAP_PROVEN"
    assert trace["first_blocked_boundary"] == "EXECUTION_GRANT_BLOCKED"
    assert "execution_grant" in trace["reachability_gap_boundaries"]


def test_valid_grant_without_candidate_budget_is_a_handoff_gap():
    candidate = _candidate()
    trace = _trace(candidate=candidate, execution_grant=_grant(candidate))

    assert trace["candidate_budget_admission_expected"] is True
    assert trace["phase_3_state"] == "NATURAL_HANDOFF_GAP_PROVEN"
    assert trace["first_blocked_boundary"] == "RUNTIME_BUDGET_BLOCKED"


def test_grant_and_budget_without_executor_call_is_a_handoff_gap():
    candidate = _candidate()
    trace = _trace(
        candidate=candidate,
        execution_grant=_grant(candidate),
        budget_admission=_budget(),
    )

    assert trace["production_executor_expected"] is True
    assert trace["phase_3_state"] == "NATURAL_HANDOFF_GAP_PROVEN"
    assert trace["first_blocked_boundary"] == "PRODUCTION_EXECUTOR_NOT_REACHED"


def test_executor_outcome_reaches_natural_e7():
    candidate = _candidate()
    grant = _grant(candidate)
    trace = _trace(
        candidate=candidate,
        execution_grant=grant,
        budget_admission=_budget(),
        production_execution={
            "execution_state": "PRODUCTION_EXECUTED",
            "production_execution_requested": True,
            "underlying_executor_called": True,
            "real_execution_performed": True,
            "run_id": "run-e4-phase3",
            "candidate_id": candidate["candidate_id"],
            "learned_object_id": LEARNED_OBJECT_ID,
            "grant_id": grant["grant_id"],
            "execution_result_id": "result-e4-phase3",
            "outcome_provenance_state": "OUTCOME_PROVENANCE_COMPLETE",
        },
    )

    assert trace["phase_3_state"] == "NATURAL_END_TO_END_REACHABILITY_PROVEN"
    assert trace["first_blocked_boundary"] == "NATURAL_E7_REACHED"
    assert trace["highest_natural_runtime_level"] == "E7"


def test_blocked_arena_with_grant_is_unauthorized_downstream_activity():
    candidate = _candidate()
    trace = _trace(
        candidate=candidate,
        arena_selection=_arena(
            selection_state="NO_SAFE_WINNER",
            selected_candidate_id=None,
            selected_candidate={},
        ),
        execution_grant=_grant(candidate),
    )

    assert trace["phase_3_state"] == "UNAUTHORIZED_DOWNSTREAM_REACHABILITY"
    assert trace["unauthorized_downstream_activity"] == "UNEXPECTED_GRANT_AFTER_BLOCK"


def test_blocked_arena_with_executor_call_is_unauthorized_execution():
    candidate = _candidate()
    trace = _trace(
        candidate=candidate,
        arena_selection=_arena(
            selection_state="TIE_REQUIRES_REVIEW",
            selected_candidate_id=None,
            selected_candidate={},
        ),
        production_execution={
            "underlying_executor_called": True,
            "real_execution_performed": True,
        },
    )

    assert trace["phase_3_state"] == "UNAUTHORIZED_DOWNSTREAM_REACHABILITY"
    assert trace["unauthorized_downstream_activity"] == (
        "UNAUTHORIZED_EXECUTOR_REACHABILITY"
    )


@pytest.mark.parametrize(
    ("expected", "observed", "gap"),
    [(False, False, False), (True, False, True), (True, True, False)],
)
def test_expected_vs_observed_gap_semantics(expected, observed, gap):
    trace = _trace(
        arena_selection=_arena() if expected else {},
        execution_grant=_grant(_candidate()) if observed else None,
    )
    row = next(
        item
        for item in trace["expected_vs_observed_reachability"]
        if item["boundary"] == "execution_grant"
    )

    assert row["expected"] is expected
    assert row["observed"] is observed
    assert row["reachability_gap"] is gap


def test_first_block_reports_only_earliest_causal_boundary():
    trace = _trace(
        sandbox_validation=_validation(
            validation_state="FAILED",
            validation_success=False,
        ),
        qualification={},
        arena_selection={},
    )

    assert trace["first_blocked_boundary"] == "SANDBOX_VALIDATION_FAILED"
    assert trace["boundary_states"]["qualification"] == "NOT_REACHED"


def test_exact_success_and_repair_success_do_not_imply_grant():
    trace = _trace(
        arena_selection=_arena(
            selection_state="TIE_REQUIRES_REVIEW",
            selected_candidate_id=None,
            selected_candidate={},
        ),
        production_outcome={
            "evaluation_result": {
                "exact_success": True,
                "accuracy": 1.0,
                "repair_success": True,
            }
        },
    )

    assert trace["grant_expected"] is False
    assert trace["first_blocked_boundary"] == "ARENA_TIE_REQUIRES_REVIEW"


def test_run_budget_finalized_does_not_imply_candidate_budget_admission():
    candidate = _candidate()
    trace = _trace(
        candidate=candidate,
        execution_grant=_grant(candidate),
        budget_admission=None,
        run_budget_state="RUNTIME_BUDGET_FINALIZED",
    )

    assert trace["run_budget_state"] == "RUNTIME_BUDGET_FINALIZED"
    assert trace["production_candidate_budget_admission_state"] == "NOT_REACHED"
    assert trace["first_blocked_boundary"] == "RUNTIME_BUDGET_BLOCKED"


def test_candidate_fingerprint_drift_and_cross_run_reuse_are_detected():
    candidate = _candidate()
    grant = _grant(candidate)
    drifted = deepcopy(grant)
    drifted["candidate_fingerprint"] = "different-fingerprint"
    drift = _trace(candidate=candidate, execution_grant=drifted)
    cross_run = _trace(candidate=candidate, execution_grant={**grant, "run_id": "other-run"})

    assert drift["candidate_lineage_state"] == "CANDIDATE_FINGERPRINT_DRIFT"
    assert cross_run["candidate_lineage_state"] == "CANDIDATE_LINEAGE_BREAK"


def test_synthetic_or_manual_evidence_cannot_satisfy_natural_e7():
    trace = _trace(
        execution_grant=_grant(_candidate()),
        budget_admission=_budget(),
        production_execution={
            "underlying_executor_called": True,
            "real_execution_performed": True,
            "outcome_provenance_state": "OUTCOME_PROVENANCE_COMPLETE",
        },
        synthetic_assistance_used=True,
        manual_grant_issuance=True,
    )

    assert trace["phase_3_state"] == "INSUFFICIENT_OBSERVABILITY"
    assert trace["first_blocked_boundary"] == "NATURAL_E7_PROOF_INVALID"


def test_execute_production_attaches_natural_handoff_trace_for_success():
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()
    grant = _grant(candidate)

    result = engine.execute_production(
        candidate=candidate,
        compiled_program={
            "steps": [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]
        },
        validation=_validation(),
        qualification=_qualification(),
        arena_selection=_arena(candidate=candidate),
        execution_grant=grant,
        budget_admission=_budget(),
        governance_state={},
        execution_context={"run_id": "run-e4-phase3", "production_execution_requested": True},
        input_grid=[[1]],
        requested_operation="replace_color",
    )

    trace = result["NATURAL_PRODUCTION_HANDOFF_TRACE"]
    assert result["real_execution_performed"] is True
    assert trace["phase_3_state"] == "NATURAL_END_TO_END_REACHABILITY_PROVEN"
    assert trace["execution_result_id"] == result["execution_result_id"]


def test_execute_production_attaches_fail_closed_trace_for_arena_tie():
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()

    result = engine.execute_production(
        candidate=candidate,
        compiled_program={"steps": []},
        validation=_validation(),
        qualification=_qualification(),
        arena_selection=_arena(
            selection_state="TIE_REQUIRES_REVIEW",
            selected_candidate_id=None,
            selected_candidate={},
        ),
        execution_grant=None,
        budget_admission=None,
        governance_state={},
        execution_context={"run_id": "run-e4-phase3", "production_execution_requested": True},
        input_grid=[[1]],
        requested_operation="replace_color",
    )

    trace = result["NATURAL_PRODUCTION_HANDOFF_TRACE"]
    assert result["real_execution_performed"] is False
    assert trace["first_blocked_boundary"] == "ARENA_TIE_REQUIRES_REVIEW"
    assert trace["grant_expected"] is False
    assert trace["production_executor_expected"] is False
    assert trace["production_executor_reached"] is False


def test_natural_handoff_trace_survives_report_projection_and_compression():
    trace = _trace(
        arena_selection=_arena(
            selection_state="TIE_REQUIRES_REVIEW",
            selected_candidate_id=None,
            selected_candidate={},
        )
    )
    compact = CompactReportBuilder().compact_context(
        {"NATURAL_PRODUCTION_HANDOFF_TRACE": trace},
        level="minimal",
    )
    rendered = DeterministicFinalReportRenderer().render(
        {"NATURAL_PRODUCTION_HANDOFF_TRACE": trace},
        report_level="normal",
    )

    assert compact["NATURAL_PRODUCTION_HANDOFF_TRACE"]["run_id"] == "run-e4-phase3"
    assert compact["NATURAL_PRODUCTION_HANDOFF_TRACE"]["candidate_id"] == (
        "candidate-e4-natural"
    )
    assert "NATURAL PRODUCTION AUTHORITY HANDOFF" in rendered
    assert "Arena Decision: TIE_REQUIRES_REVIEW" in rendered
