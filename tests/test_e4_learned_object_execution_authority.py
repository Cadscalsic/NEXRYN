from copy import deepcopy

from runtime.security import LearnedObjectExecutionGrantAuthority


LEARNED_OBJECT_ID = "program-6097823aa7c9afc0"


def _candidate(**overrides):
    data = {
        "candidate_id": "adaptive_reuse_0",
        "learned_object_id": LEARNED_OBJECT_ID,
        "source_learned_object_id": LEARNED_OBJECT_ID,
        "learned_object_type": "PROGRAM",
        "reuse_proposal_id": "adaptive_reuse:0",
        "permitted_operations": ["replace_color"],
    }
    data.update(overrides)
    return data


def _learned_object(**overrides):
    data = {
        "learned_object_id": LEARNED_OBJECT_ID,
        "canonical_provenance": {
            "retrieval_state": "RETRIEVED",
            "proposal_id": "adaptive_reuse:0",
            "source_run_id": "ORIGIN_NOT_OBSERVABLE",
        },
    }
    data.update(overrides)
    return data


def _arena(**overrides):
    data = {
        "arena_selection_id": "arena_selection_1",
        "selection_state": "WINNER_SELECTED",
        "selected_candidate_id": "adaptive_reuse_0",
    }
    data.update(overrides)
    return data


def _validation(**overrides):
    data = {
        "validation_id": "sandbox_validation_1",
        "validation_state": "SANDBOX_VALIDATION_PASSED",
        "evidence_sufficient_for_execution_use": True,
        "evidence_acceptance_state": "ACCEPTED",
    }
    data.update(overrides)
    return data


def _qualification(**overrides):
    data = {
        "qualification_id": "qualification_1",
        "qualification_state": "QUALIFIED",
        "governance_constraints_satisfied": True,
    }
    data.update(overrides)
    return data


def _scope(**overrides):
    data = {
        "operation": "replace_color",
        "max_steps": 1,
    }
    data.update(overrides)
    return data


def _budget(**overrides):
    data = {
        "runtime_budget_state": "RUNTIME_BUDGET_FINALIZED",
        "route_budget_enforcement_state": "ROUTE_BUDGET_ADMITTED",
        "realized_overrun_state": "NO_REALIZED_OVERRUN",
        "violation_reason": "NONE",
    }
    data.update(overrides)
    return data


def _grant():
    return LearnedObjectExecutionGrantAuthority().issue_grant(
        run_id="run_current",
        candidate=_candidate(),
        learned_object=_learned_object(),
        arena_selection=_arena(),
        validation=_validation(),
        qualification=_qualification(),
        execution_scope=_scope(),
        budget_admission=_budget(),
    )


def test_learned_object_execution_grant_contract_is_run_scoped_and_nonpersistent():
    contract = LearnedObjectExecutionGrantAuthority().contract()

    assert contract["grant_object"] == "LearnedObjectExecutionGrant"
    assert contract["authority"] == "EXECUTION"
    assert contract["scope"] == "CURRENT_RUN_ONLY"
    assert contract["persistent"] is False
    assert contract["inheritable"] is False
    assert contract["promotable"] is False
    assert contract["transferable"] is False
    assert contract["revocable"] is True
    assert "runtime_budget_available" in contract["required_preconditions"]


def test_positive_control_issues_and_consumes_grant_with_budget_admission():
    authority = LearnedObjectExecutionGrantAuthority()
    grant = _grant()

    consumption = authority.validate_for_consumption(
        grant,
        run_id="run_current",
        candidate_id="adaptive_reuse_0",
        learned_object_id=LEARNED_OBJECT_ID,
        requested_operation="replace_color",
        budget_admission=_budget(),
    )

    assert grant["grant_state"] == "ISSUED"
    assert grant["authority"] == "EXECUTION"
    assert grant["persistent"] is False
    assert consumption["production_execution_authorized"] is True
    assert consumption["budget_authority_composed"] is True


def test_selected_candidate_without_execution_grant_fails_closed():
    consumption = LearnedObjectExecutionGrantAuthority().validate_for_consumption(
        None,
        run_id="run_current",
        candidate_id="adaptive_reuse_0",
        learned_object_id=LEARNED_OBJECT_ID,
        requested_operation="replace_color",
        budget_admission=_budget(),
    )

    assert consumption["production_execution_authorized"] is False
    assert consumption["denial_reason"] == "GRANT_MISSING"


def test_no_safe_winner_blocks_grant_before_execution_authority():
    grant = LearnedObjectExecutionGrantAuthority().issue_grant(
        run_id="run_current",
        candidate=_candidate(),
        learned_object=_learned_object(),
        arena_selection=_arena(selection_state="NO_SAFE_WINNER"),
        validation=_validation(),
        qualification=_qualification(),
        execution_scope=_scope(),
        budget_admission=_budget(),
    )

    assert grant["grant_state"] == "BLOCKED"
    assert "arena_selection_valid" in grant["block_reason"]
    assert grant["production_execution_authorized"] is False


def test_validation_is_not_execution_authority():
    grant = LearnedObjectExecutionGrantAuthority().issue_grant(
        run_id="run_current",
        candidate=_candidate(),
        learned_object=_learned_object(),
        arena_selection=_arena(),
        validation=_validation(),
        qualification=_qualification(qualification_state="NOT_QUALIFIED"),
        execution_scope=_scope(),
        budget_admission=_budget(),
    )

    assert grant["grant_state"] == "BLOCKED"
    assert "candidate_qualified" in grant["block_reason"]


def test_authority_separation_attacks_fail_closed_after_grant_issue():
    authority = LearnedObjectExecutionGrantAuthority()
    grant = _grant()

    attacks = {
        "grant_for_different_candidate": {
            "candidate_id": "other_candidate",
            "learned_object_id": LEARNED_OBJECT_ID,
            "run_id": "run_current",
            "requested_operation": "replace_color",
            "budget_admission": _budget(),
            "reason": "CANDIDATE_ID_SCOPE_MISMATCH",
        },
        "grant_for_different_learned_object": {
            "candidate_id": "adaptive_reuse_0",
            "learned_object_id": "program-other",
            "run_id": "run_current",
            "requested_operation": "replace_color",
            "budget_admission": _budget(),
            "reason": "LEARNED_OBJECT_ID_SCOPE_MISMATCH",
        },
        "grant_from_different_run": {
            "candidate_id": "adaptive_reuse_0",
            "learned_object_id": LEARNED_OBJECT_ID,
            "run_id": "other_run",
            "requested_operation": "replace_color",
            "budget_admission": _budget(),
            "reason": "RUN_ID_SCOPE_MISMATCH",
        },
        "grant_exceeding_execution_scope": {
            "candidate_id": "adaptive_reuse_0",
            "learned_object_id": LEARNED_OBJECT_ID,
            "run_id": "run_current",
            "requested_operation": "delete_memory",
            "budget_admission": _budget(),
            "reason": "EXECUTION_SCOPE_EXCEEDED",
        },
        "grant_exceeding_runtime_budget": {
            "candidate_id": "adaptive_reuse_0",
            "learned_object_id": LEARNED_OBJECT_ID,
            "run_id": "run_current",
            "requested_operation": "replace_color",
            "budget_admission": _budget(
                runtime_budget_state="RUNTIME_BUDGET_INTEGRITY_FAILED",
                realized_overrun_state="REALIZED_OVERRUN",
                violation_reason="AUTHORITATIVE_RUNTIME_BUDGET_EXCEEDED",
            ),
            "reason": "BUDGET_ADMISSION_GAP",
        },
    }

    for attack in attacks.values():
        reason = attack.pop("reason")
        result = authority.validate_for_consumption(grant, **attack)
        assert result["production_execution_authorized"] is False
        assert result["denial_reason"] == reason


def test_revoked_copied_and_persisted_historical_grants_fail_closed():
    authority = LearnedObjectExecutionGrantAuthority()
    grant = _grant()
    revoked = authority.revoke(grant)
    copied = deepcopy(grant)
    copied["candidate_id"] = "adaptive_reuse_0_copied"
    persisted = deepcopy(grant)
    persisted["persistent"] = True

    revoked_result = authority.validate_for_consumption(
        revoked,
        run_id="run_current",
        candidate_id="adaptive_reuse_0",
        learned_object_id=LEARNED_OBJECT_ID,
        requested_operation="replace_color",
        budget_admission=_budget(),
    )
    copied_result = authority.validate_for_consumption(
        copied,
        run_id="run_current",
        candidate_id="adaptive_reuse_0_copied",
        learned_object_id=LEARNED_OBJECT_ID,
        requested_operation="replace_color",
        budget_admission=_budget(),
    )
    persisted_result = authority.validate_for_consumption(
        persisted,
        run_id="run_current",
        candidate_id="adaptive_reuse_0",
        learned_object_id=LEARNED_OBJECT_ID,
        requested_operation="replace_color",
        budget_admission=_budget(),
    )

    assert revoked_result["denial_reason"] == "GRANT_REVOKED"
    assert copied_result["denial_reason"] == "GRANT_FINGERPRINT_MISMATCH"
    assert persisted_result["denial_reason"] == "PERSISTED_HISTORICAL_GRANT_FORBIDDEN"


def test_pregrant_boundary_attacks_do_not_issue_grant():
    authority = LearnedObjectExecutionGrantAuthority()
    cases = [
        ("persisted_object_without_retrieval", {"learned_object": _learned_object(canonical_provenance={})}, "learned_object_provenance_valid"),
        ("retrieved_object_without_candidate_materialization", {"candidate": {}}, "candidate_materialized"),
        ("candidate_without_validation", {"validation": {}}, "sandbox_validation_passed"),
        ("retrieved_candidate_without_evidence", {"validation": _validation(evidence_sufficient_for_execution_use=False, evidence_acceptance_state="INSUFFICIENT")}, "evidence_sufficient_for_execution_use"),
    ]

    for _, overrides, missing in cases:
        inputs = {
            "run_id": "run_current",
            "candidate": _candidate(),
            "learned_object": _learned_object(),
            "arena_selection": _arena(),
            "validation": _validation(),
            "qualification": _qualification(),
            "execution_scope": _scope(),
            "budget_admission": _budget(),
        }
        inputs.update(overrides)
        grant = authority.issue_grant(**inputs)
        assert grant["grant_state"] == "BLOCKED"
        assert missing in grant["block_reason"]
