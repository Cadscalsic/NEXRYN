from copy import deepcopy

from runtime.execution import ExecutableIntelligenceEngine, ExecutionMemory
from runtime.security import LearnedObjectExecutionGrantAuthority


LEARNED_OBJECT_ID = "program-fixture-e4-phase2"


def _candidate(**overrides):
    data = {
        "candidate_id": "fixture_candidate_1",
        "learned_object_id": LEARNED_OBJECT_ID,
        "source_learned_object_id": LEARNED_OBJECT_ID,
        "source": "adaptive_reuse",
        "operation": "replace_color",
        "permitted_operations": ["replace_color"],
        "canonical_provenance": {
            "persisted_learned_object": True,
            "retrieval_state": "RETRIEVED",
            "retrieval_id": "retrieval_fixture_1",
        },
        "program": {
            "steps": [
                {
                    "operation": "replace_color",
                    "parameters": {"color_mapping": {1: 2}},
                }
            ],
        },
    }
    data.update(overrides)
    return data


def _learned_object(**overrides):
    data = {
        "learned_object_id": LEARNED_OBJECT_ID,
        "canonical_provenance": {
            "persisted_learned_object": True,
            "retrieval_state": "RETRIEVED",
            "retrieval_id": "retrieval_fixture_1",
        },
    }
    data.update(overrides)
    return data


def _arena(candidate=None, **overrides):
    candidate = candidate or _candidate()
    data = {
        "arena_selection_id": "arena_fixture_1",
        "selection_state": "WINNER_SELECTED",
        "execution_mode": "real",
        "selected_candidate_id": candidate["candidate_id"],
        "selected_candidate": candidate,
    }
    data.update(overrides)
    return data


def _validation(**overrides):
    data = {
        "validation_id": "sandbox_fixture_1",
        "validation_state": "SANDBOX_VALIDATION_PASSED",
        "validation_success": True,
        "evidence_sufficient_for_execution_use": True,
        "evidence_acceptance_state": "ACCEPTED",
    }
    data.update(overrides)
    return data


def _qualification(**overrides):
    data = {
        "qualification_id": "qualification_fixture_1",
        "qualification_state": "QUALIFIED",
        "governance_constraints_satisfied": True,
    }
    data.update(overrides)
    return data


def _budget(run_id="run_phase2", **overrides):
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


def _scope(**overrides):
    data = {"operation": "replace_color", "max_steps": 2}
    data.update(overrides)
    return data


def _grant(engine=None, candidate=None, run_id="run_phase2", scope=None, budget=None):
    engine = engine or ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = candidate or _candidate()
    grant_candidate = deepcopy(candidate)
    grant_candidate["candidate_fingerprint"] = engine._candidate_fingerprint(candidate)
    return LearnedObjectExecutionGrantAuthority().issue_grant(
        run_id=run_id,
        candidate=grant_candidate,
        learned_object=_learned_object(),
        arena_selection=_arena(candidate),
        validation=_validation(),
        qualification=_qualification(),
        execution_scope=scope or _scope(),
        budget_admission=budget or _budget(run_id),
    )


def test_lawful_learned_object_candidate_reaches_existing_production_executor():
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()
    grant = _grant(engine=engine, candidate=candidate)

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
        budget_admission=_budget(),
        governance_context={},
        execution_context={"run_id": "run_phase2"},
    )

    production = result["PRODUCTION_EXECUTION_RESULT"]
    report = result["EXECUTABLE_INTELLIGENCE_REPORT"]

    assert production["execution_state"] == "PRODUCTION_EXECUTED"
    assert production["real_execution_performed"] is True
    assert production["underlying_executor_called"] is True
    assert production["grant_state_after"] == "CONSUMED"
    assert production["outcome_provenance_state"] == "OUTCOME_PROVENANCE_COMPLETE"
    assert production["outcome_provenance"]["grant_id"] == production["grant_id"]
    assert production["outcome_provenance"]["run_id"] == "run_phase2"
    assert production["outcome_provenance"]["candidate_id"] == "fixture_candidate_1"
    assert production["outcome_provenance"]["learned_object_id"] == LEARNED_OBJECT_ID
    assert production["outcome_provenance"]["actual_operation"] == "replace_color"
    assert production["execution_receipt"]["authority"] == "NONE"
    assert production["execution_receipt"]["reusable_execution_authority"] is False
    assert production["execution_receipt"]["execution_grant_id"] == production["grant_id"]
    assert "ExecutableIntelligenceEngine.execute_production" in production[
        "executor_identity"
    ]
    assert production["budget_context"]["budget_admission_id"] == "budget:run_phase2"
    assert production["result"]["output_grid"] == [[2, 2], [0, 0]]
    assert report["real_execution_performed"] is True


def test_production_executor_attacks_fail_before_underlying_operation():
    attacks = []
    base_engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    base_candidate = _candidate()
    valid_grant = _grant(engine=base_engine, candidate=base_candidate)

    attacks.append(("missing_grant", None, {}, "GRANT_MISSING"))
    attacks.append(("wrong_run", valid_grant, {"run_id": "other_run"}, "RUN_ID_SCOPE_MISMATCH"))
    attacks.append(
        (
            "wrong_candidate",
            valid_grant,
            {"candidate": _candidate(candidate_id="other_candidate")},
            "CANDIDATE_ID_SCOPE_MISMATCH",
        )
    )
    attacks.append(
        (
            "wrong_object",
            valid_grant,
            {
                "candidate": _candidate(
                    learned_object_id="program-other",
                    source_learned_object_id="program-other",
                )
            },
            "LEARNED_OBJECT_ID_SCOPE_MISMATCH",
        )
    )
    attacks.append(
        (
            "wrong_operation",
            _grant(scope=_scope(operation="replace_color")),
            {"operation": "delete_memory"},
            "EXECUTION_SCOPE_EXCEEDED",
        )
    )
    attacks.append(
        (
            "scope_excess",
            _grant(scope=_scope(max_steps=1)),
            {"request": {"requested_scope": {"operation": "replace_color", "max_steps": 2}}},
            "SCOPE_BINDING_VALID",
        )
    )
    attacks.append(
        (
            "revoked",
            LearnedObjectExecutionGrantAuthority().revoke(_grant()),
            {},
            "GRANT_REVOKED",
        )
    )
    attacks.append(
        (
            "persisted_replay",
            {**_grant(), "persistent": True},
            {},
            "PERSISTED_HISTORICAL_GRANT_FORBIDDEN",
        )
    )
    malformed = deepcopy(_grant())
    malformed.pop("grant_fingerprint", None)
    attacks.append(("malformed_grant", malformed, {}, "GRANT_FINGERPRINT_MISMATCH"))
    expired = deepcopy(_grant())
    expired["grant_state"] = "EXPIRED"
    expired["grant_fingerprint"] = LearnedObjectExecutionGrantAuthority()._fingerprint(expired)
    attacks.append(("expired_grant", expired, {}, "EXPIRED"))
    attacks.append(("missing_budget", _grant(), {"budget": None}, "BUDGET_ADMISSION_MISSING"))
    attacks.append(
        (
            "budget_from_other_run",
            _grant(),
            {"budget": _budget("other_run")},
            "BUDGET_RUN_SCOPE_MISMATCH",
        )
    )
    attacks.append(
        (
            "budget_insufficient",
            _grant(),
            {
                "budget": _budget(
                    runtime_budget_state="RUNTIME_BUDGET_INTEGRITY_FAILED",
                    route_budget_enforcement_state="ROUTE_BUDGET_EXCEEDED",
                    realized_overrun_state="REALIZED_OVERRUN",
                    violation_reason="AUTHORITATIVE_RUNTIME_BUDGET_EXCEEDED",
                )
            },
            "BUDGET_ADMISSION_GAP",
        )
    )
    attacks.append(
        (
            "stale_budget",
            _grant(),
            {"budget": _budget(budget_state="STALE", stale=True)},
            "BUDGET_ADMISSION_GAP",
        )
    )
    attacks.append(
        (
            "qualification_missing",
            _grant(),
            {"qualification": {}},
            "QUALIFICATION_MISSING",
        )
    )
    attacks.append(
        (
            "qualification_failed",
            _grant(),
            {"qualification": _qualification(qualification_state="FAILED")},
            "QUALIFICATION_FAILED",
        )
    )
    attacks.append(
        (
            "no_safe_winner",
            _grant(),
            {"arena": _arena(selection_state="NO_SAFE_WINNER", selected_candidate_id=None, selected_candidate={})},
            "ARENA_NO_EXECUTABLE_WINNER",
        )
    )
    attacks.append(
        (
            "different_arena_selection",
            _grant(),
            {
                "arena": _arena(
                    arena_selection_id="arena_fixture_other",
                )
            },
            "ARENA_SELECTION_IDENTITY_MISMATCH",
        )
    )
    attacks.append(
        (
            "different_qualification_identity",
            _grant(),
            {
                "qualification": _qualification(
                    qualification_id="qualification_fixture_other"
                )
            },
            "QUALIFICATION_IDENTITY_MISMATCH",
        )
    )
    no_provenance = deepcopy(_grant())
    no_provenance["canonical_provenance"] = {}
    no_provenance["grant_fingerprint"] = LearnedObjectExecutionGrantAuthority()._fingerprint(no_provenance)
    attacks.append(
        (
            "missing_provenance",
            no_provenance,
            {"candidate": _candidate(canonical_provenance={})},
            "SOURCE_PROVENANCE_MISSING",
        )
    )
    attacks.append(
        (
            "candidate_mutated",
            _grant(engine=base_engine, candidate=base_candidate),
            {"candidate": _candidate(extra_field="mutated_after_grant")},
            "CANDIDATE_MUTATED_AFTER_GRANT",
        )
    )
    attacks.append(
        (
            "program_fingerprint_changed",
            _grant(
                scope=_scope(
                    program_fingerprint="program_fingerprint_authorized_before_mutation"
                )
            ),
            {},
            "PROGRAM_FINGERPRINT_CHANGED",
        )
    )
    attacks.append(
        (
            "governance_blocked_after_grant",
            _grant(),
            {"governance": {"identity_governance": "REVOKED"}},
            "GOVERNANCE_BLOCKED_AFTER_GRANT",
        )
    )

    for _, grant, overrides, expected_reason in attacks:
        engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
        candidate = overrides.get("candidate") or _candidate()
        production = engine.execute_production(
            candidate=candidate,
            compiled_program={
                "steps": [
                    {
                        "operation": overrides.get("operation", "replace_color"),
                        "parameters": {"color_mapping": {1: 2}},
                    }
                ],
                "step_count": 1,
                "execution_scope": "local",
            },
            validation=_validation(),
            qualification=overrides.get("qualification", _qualification()),
            arena_selection=overrides.get("arena", _arena(candidate)),
            execution_grant=grant,
            budget_admission=overrides.get("budget", _budget()),
            production_execution_request=overrides.get("request"),
            governance_state=overrides.get("governance", {}),
            execution_context={
                "run_id": overrides.get("run_id", "run_phase2"),
                "production_execution_requested": True,
            },
            input_grid=[[1]],
            requested_operation=overrides.get("operation", "replace_color"),
        )

        assert production["real_execution_performed"] is False
        assert production["underlying_executor_called"] is False
        assert production["underlying_executor_call_count"] == 0
        assert production["denial_reason"] == expected_reason


def test_consumed_grant_cannot_execute_twice():
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate()
    grant = _grant(engine=engine, candidate=candidate)

    first = engine.execute_production(
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
        execution_grant=grant,
        budget_admission=_budget(),
        governance_state={},
        execution_context={"run_id": "run_phase2", "production_execution_requested": True},
        input_grid=[[1]],
        requested_operation="replace_color",
    )
    second = engine.execute_production(
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
        execution_grant=grant,
        budget_admission=_budget(),
        governance_state={},
        execution_context={"run_id": "run_phase2", "production_execution_requested": True},
        input_grid=[[1]],
        requested_operation="replace_color",
    )

    assert first["execution_state"] == "PRODUCTION_EXECUTED"
    assert second["real_execution_performed"] is False
    assert second["denial_reason"] == "DENIED_GRANT_ALREADY_CONSUMED"
    assert second["underlying_executor_call_count"] == 1


def test_real_learned_object_no_safe_winner_remains_unexecuted():
    real_id = "program-6097823aa7c9afc0"
    engine = ExecutableIntelligenceEngine(memory=ExecutionMemory())
    candidate = _candidate(
        candidate_id="adaptive_reuse:0",
        learned_object_id=real_id,
        source_learned_object_id=real_id,
    )

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

    assert result["production_admission_state"] == "DENIED"
    assert result["denial_reason"] == "QUALIFICATION_MISSING"
    assert result["real_execution_performed"] is False
    assert result["underlying_executor_called"] is False
