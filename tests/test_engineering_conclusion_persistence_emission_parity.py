import json

from runtime.reporting.engineering_conclusion_integrity import (
    STABLE_SEMANTIC_FIELDS,
    engineering_conclusion_integrity_evaluator,
)
from runtime.reporting.final_report_renderer import DeterministicFinalReportRenderer


def _state(
    *,
    run_id: str = "run_parity",
    plan_id: str = "plan_parity",
    raw_not_applicable: bool = False,
    raw_id: str | None = None,
    accepted: bool = True,
) -> dict:
    state = {
        "run_id": run_id,
        "CANONICAL_EXECUTION_PLAN": {"execution_plan_id": plan_id},
    }
    if raw_not_applicable:
        state["RAW_RESULT_APPLICABILITY_REPORT"] = {
            "raw_result_applicability_state": "RAW_RESULT_NOT_APPLICABLE",
        }
    if raw_id is not None:
        state["VALIDATION_TASK_EXECUTION_REPORT"] = {
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": raw_id,
        }
    elif accepted:
        state["VALIDATION_EVIDENCE_EVALUATION_REPORT"] = {
            "evidence_acceptance_state": "ACCEPTED",
        }
    return state


def _conclusion(**kwargs):
    state = _state(**kwargs)
    return engineering_conclusion_integrity_evaluator.create_authoritative_conclusion(
        state,
        runtime_metadata={"execution_id": state["run_id"]},
    )


def test_applicable_persistence_write_readback_and_emission_match(tmp_path):
    conclusion = _conclusion()
    artifact = tmp_path / "conclusion.json"

    persistence = engineering_conclusion_integrity_evaluator.persist_conclusion(
        conclusion,
        artifact,
    )
    readback = engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
        artifact,
    )
    persistence_integrity = (
        engineering_conclusion_integrity_evaluator.evaluate_persistence_integrity(
            conclusion,
            readback,
        )
    )
    emission = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    parity = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        readback,
        emission,
        authoritative=conclusion,
    )
    emission_integrity = (
        engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
            conclusion,
            emission,
        )
    )

    assert persistence["persistence_applicability"] == "APPLICABLE"
    assert persistence["persistence_write_attempted"] is True
    assert persistence["persistence_write_completed"] is True
    assert persistence["persistence_integrity"] == "NOT_EVALUATED"
    assert readback["persistence_readback_attempted"] is True
    assert readback["persistence_readback_completed"] is True
    assert persistence_integrity["persistence_integrity"] == "VERIFIED"
    assert persistence_integrity["persistence_integrity_reason"] == (
        "authoritative_and_persisted_readback_payloads_match"
    )
    assert parity["emission_integrity"] == "EMISSION_VERIFIED"
    assert emission_integrity["emission_integrity"] == "EMISSION_VERIFIED"
    assert emission_integrity["emission_integrity_reason"] == (
        "authoritative_and_emitted_payloads_match"
    )
    assert emission_integrity["emission_conflict_count"] == 0
    assert parity["persistence_matches_emission"] is True
    assert parity["persistence_emission_conflict_count"] == 0
    assert persistence["conclusion_fingerprint"] == parity["stored_fingerprint"]
    assert parity["stored_fingerprint"] == parity["recomputed_readback_fingerprint"]
    assert parity["stored_fingerprint"] == parity["emitted_fingerprint"]
    assert emission_integrity["authoritative_fingerprint"] == (
        emission_integrity["emitted_fingerprint"]
    )


def test_persistence_not_applicable_is_not_reported_as_verified():
    conclusion = _conclusion(raw_not_applicable=True, accepted=False)
    evaluated = (
        engineering_conclusion_integrity_evaluator
        .evaluate_persistence_applicability(conclusion)
    )
    emission = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    parity = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        None,
        emission,
    )

    assert evaluated["conclusion_state"] == "NOT_APPLICABLE"
    assert evaluated["persistence_applicability"] == "NOT_APPLICABLE"
    assert parity["persistence_integrity"] == "NOT_APPLICABLE"
    assert parity["emission_integrity"] == "NOT_EVALUATED"
    assert parity["persistence_matches_emission"] == "NOT_APPLICABLE"


def test_substantive_not_applicable_does_not_force_persistence_applicability(tmp_path):
    conclusion = _conclusion(raw_not_applicable=True, accepted=False)
    not_required = (
        engineering_conclusion_integrity_evaluator
        .evaluate_persistence_applicability(conclusion)
    )
    required = (
        engineering_conclusion_integrity_evaluator
        .evaluate_persistence_applicability(
            conclusion,
            artifact_path=tmp_path / "conclusion.json",
        )
    )

    assert not_required["conclusion_state"] == "NOT_APPLICABLE"
    assert not_required["persistence_applicability"] == "NOT_APPLICABLE"
    assert required["conclusion_state"] == "NOT_APPLICABLE"
    assert required["persistence_applicability"] == "APPLICABLE"


def test_missing_persisted_stable_field_causes_parity_failure():
    conclusion = _conclusion()
    persisted = engineering_conclusion_integrity_evaluator.stable_payload(conclusion)
    persisted.pop("root_cause")
    emission = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )

    parity = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        persisted,
        emission,
    )

    assert parity["persistence_integrity"] == "FAILED"
    assert "root_cause" in parity["persistence_emission_conflict_fields"]


def test_missing_emitted_stable_field_causes_parity_failure():
    conclusion = _conclusion()
    persisted = engineering_conclusion_integrity_evaluator.stable_payload(conclusion)
    emitted = engineering_conclusion_integrity_evaluator.stable_payload(conclusion)
    emitted.pop("recommended_action")

    comparison = engineering_conclusion_integrity_evaluator.compare_semantic_payloads(
        persisted,
        emitted,
    )

    assert comparison["comparison_state"] == "SEMANTIC_PAYLOAD_MISMATCH"
    assert any(row["field"] == "recommended_action" for row in comparison["mismatches"])


def test_write_success_without_readback_does_not_verify(tmp_path):
    conclusion = _conclusion()
    artifact = tmp_path / "conclusion.json"

    written = engineering_conclusion_integrity_evaluator.persist_conclusion(
        conclusion,
        artifact,
    )
    integrity = engineering_conclusion_integrity_evaluator.evaluate_persistence_integrity(
        conclusion,
        None,
    )

    assert written["persistence_write_completed"] is True
    assert artifact.exists()
    assert written["persistence_integrity"] == "NOT_EVALUATED"
    assert integrity["persistence_integrity"] == "FAILED"
    assert integrity["persistence_integrity_reason"] == (
        "persistence_readback_not_available"
    )


def test_missing_and_corrupt_persistence_artifacts_fail_truthfully(tmp_path):
    conclusion = _conclusion()
    missing = tmp_path / "missing.json"
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not-json", encoding="utf-8")

    missing_readback = (
        engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
            missing,
        )
    )
    corrupt_readback = (
        engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
            corrupt,
        )
    )
    missing_result = (
        engineering_conclusion_integrity_evaluator.evaluate_persistence_integrity(
            conclusion,
            missing_readback,
        )
    )
    corrupt_result = (
        engineering_conclusion_integrity_evaluator.evaluate_persistence_integrity(
            conclusion,
            corrupt_readback,
        )
    )

    assert missing_result["persistence_integrity"] == "FAILED"
    assert missing_result["persistence_integrity_reason"] == (
        "persistence_artifact_missing"
    )
    assert corrupt_result["persistence_integrity"] == "FAILED"
    assert corrupt_result["persistence_integrity_reason"] == (
        "persistence_readback_corrupt_json"
    )


def test_failing_writer_does_not_fall_back_to_verified(tmp_path):
    conclusion = _conclusion()
    blocked_parent = tmp_path / "not_a_directory"
    blocked_parent.write_text("blocks mkdir", encoding="utf-8")

    written = engineering_conclusion_integrity_evaluator.persist_conclusion(
        conclusion,
        blocked_parent / "conclusion.json",
    )

    assert written["persistence_write_attempted"] is True
    assert written["persistence_write_completed"] is False
    assert written["persistence_integrity"] == "FAILED"
    assert written["persistence_integrity_reason"].startswith(
        "persistence_write_failed:"
    )


def test_persisted_mutation_fails_even_with_matching_stored_fingerprint(tmp_path):
    conclusion = _conclusion()
    artifact = tmp_path / "conclusion.json"
    engineering_conclusion_integrity_evaluator.persist_conclusion(
        conclusion,
        artifact,
    )
    persisted = engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
        artifact,
    )
    persisted["root_cause"] = "mutated_after_write"

    result = engineering_conclusion_integrity_evaluator.evaluate_persistence_integrity(
        conclusion,
        persisted,
    )

    assert result["persistence_integrity"] == "FAILED"
    assert "root_cause" in result["persistence_emission_conflict_fields"]
    assert "conclusion_fingerprint" in result["persistence_emission_conflict_fields"]
    assert result["stored_fingerprint"] == conclusion["conclusion_fingerprint"]
    assert result["recomputed_readback_fingerprint"] != (
        conclusion["conclusion_fingerprint"]
    )


def test_structured_payload_availability_without_comparison_does_not_verify():
    conclusion = _conclusion()
    emission = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    result = engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
        conclusion,
        None,
    )

    assert "emission_integrity" not in emission
    assert "emission_integrity_reason" not in emission
    assert result["emission_integrity"] == "NOT_EVALUATED"
    assert result["emission_integrity_reason"] == (
        "structured_emission_payload_not_available"
    )


def test_missing_mutated_and_defaulted_emission_fields_fail():
    conclusion = _conclusion()
    emitted = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    missing = dict(emitted)
    missing.pop("root_cause")
    defaulted = {**emitted, "recommended_action": "none"}
    mutated = {**emitted, "responsible_area": "FOREIGN_COMPONENT"}

    missing_result = engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
        conclusion,
        missing,
    )
    defaulted_result = engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
        conclusion,
        defaulted,
    )
    mutated_result = engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
        conclusion,
        mutated,
    )

    assert missing_result["emission_integrity"] == "EMISSION_FAILED"
    assert "root_cause" in missing_result["emission_conflict_fields"]
    assert defaulted_result["emission_integrity"] == "EMISSION_FAILED"
    assert "recommended_action" in defaulted_result["emission_conflict_fields"]
    assert mutated_result["emission_integrity"] == "EMISSION_FAILED"
    assert "responsible_area" in mutated_result["emission_conflict_fields"]


def test_emission_run_and_execution_plan_mismatch_fail():
    conclusion = _conclusion(run_id="run_current", plan_id="plan_current")
    emitted = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    wrong_run = {
        **emitted,
        "authoritative_run_id": "run_previous",
        "conclusion_run_id": "run_previous",
    }
    wrong_plan = {
        **emitted,
        "authoritative_execution_plan_id": "plan_previous",
    }

    run_result = engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
        conclusion,
        wrong_run,
    )
    plan_result = engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
        conclusion,
        wrong_plan,
    )

    assert run_result["emission_integrity"] == "EMISSION_FAILED"
    assert run_result["binding_state"] == "RUN_ID_MISMATCH_REJECTED"
    assert "authoritative_run_id" in run_result["emission_conflict_fields"]
    assert plan_result["emission_integrity"] == "EMISSION_FAILED"
    assert plan_result["binding_state"] == "EXECUTION_PLAN_ID_MISMATCH_REJECTED"
    assert "authoritative_execution_plan_id" in plan_result["emission_conflict_fields"]


def test_emission_raw_result_id_rules_match_applicability_contract():
    applicable = _conclusion(raw_id="raw_result_current", accepted=False)
    applicable_emitted = (
        engineering_conclusion_integrity_evaluator.structured_emission_payload(
            applicable,
        )
    )
    wrong_raw = {
        **applicable_emitted,
        "canonical_raw_result_id": "raw_result_foreign",
    }
    not_applicable = _conclusion(
        raw_not_applicable=True,
        raw_id="raw_result_should_not_bind",
        accepted=False,
    )
    not_applicable_emitted = (
        engineering_conclusion_integrity_evaluator.structured_emission_payload(
            not_applicable,
        )
    )

    wrong_raw_result = (
        engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
            applicable,
            wrong_raw,
        )
    )
    not_applicable_result = (
        engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
            not_applicable,
            not_applicable_emitted,
        )
    )

    assert wrong_raw_result["emission_integrity"] == "EMISSION_FAILED"
    assert "canonical_raw_result_id" in wrong_raw_result["emission_conflict_fields"]
    assert not_applicable_emitted["canonical_raw_result_id"] is None
    assert not_applicable_result["emission_integrity"] == "EMISSION_VERIFIED"


def test_default_substituted_and_mutated_fields_fail_but_formatting_does_not():
    conclusion = _conclusion()
    not_applicable = _conclusion(raw_not_applicable=True, accepted=False)
    emission = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    not_applicable_emission = (
        engineering_conclusion_integrity_evaluator.structured_emission_payload(
            not_applicable,
        )
    )
    defaulted = {**not_applicable_emission, "root_cause": "none"}
    mutated = {**emission, "authoritative_run_id": "run_foreign"}
    formatted = {**emission, "recommended_action": "continue_with_next_governed_runtime_stage\n"}

    defaulted_result = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        defaulted,
        not_applicable_emission,
    )
    mutated_result = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        mutated,
        emission,
    )
    formatted_result = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        formatted,
        emission,
    )

    assert defaulted_result["persistence_integrity"] == "FAILED"
    assert mutated_result["binding_state"] == "RUN_ID_MISMATCH_REJECTED"
    assert formatted_result["persistence_matches_emission"] is True


def test_previous_run_and_execution_plan_mismatch_cannot_bind():
    current = _conclusion(run_id="run_current", plan_id="plan_current")
    previous = {**engineering_conclusion_integrity_evaluator.stable_payload(current)}
    previous["authoritative_run_id"] = "run_previous"
    previous["conclusion_run_id"] = "run_previous"
    wrong_plan = {**engineering_conclusion_integrity_evaluator.stable_payload(current)}
    wrong_plan["authoritative_execution_plan_id"] = "plan_previous"

    previous_result = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        previous,
        engineering_conclusion_integrity_evaluator.structured_emission_payload(current),
    )
    plan_result = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        wrong_plan,
        engineering_conclusion_integrity_evaluator.structured_emission_payload(current),
    )

    assert previous_result["binding_state"] == "RUN_ID_MISMATCH_REJECTED"
    assert plan_result["binding_state"] == "EXECUTION_PLAN_ID_MISMATCH_REJECTED"


def test_canonical_raw_result_id_mismatch_detected_when_identity_applies():
    conclusion = _conclusion(raw_id="raw_result_current", accepted=False)
    emission = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    persisted = {**emission, "canonical_raw_result_id": "raw_result_foreign"}

    parity = engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        persisted,
        emission,
    )

    assert "canonical_raw_result_id" in parity["persistence_emission_conflict_fields"]


def test_absent_raw_result_id_is_valid_when_raw_result_not_applicable():
    conclusion = _conclusion(
        raw_not_applicable=True,
        raw_id="raw_result_should_not_bind",
        accepted=False,
    )
    payload = engineering_conclusion_integrity_evaluator.stable_payload(conclusion)

    assert conclusion["conclusion_state"] == "NOT_APPLICABLE"
    assert payload["canonical_raw_result_id"] is None
    assert conclusion["next_gate"] == "none"


def test_repeated_readback_binding_and_rendering_preserve_semantics(tmp_path):
    conclusion = _conclusion(raw_not_applicable=True, accepted=False)
    artifact = tmp_path / "conclusion.json"
    engineering_conclusion_integrity_evaluator.persist_conclusion(conclusion, artifact)

    first_read = engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
        artifact,
    )
    second_read = engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
        artifact,
    )
    first_bound = engineering_conclusion_integrity_evaluator.bind_to_canonical_report(
        first_read,
        report_state=_state(raw_not_applicable=True, accepted=False),
        runtime_metadata={"execution_id": "run_parity"},
    )
    second_bound = engineering_conclusion_integrity_evaluator.bind_to_canonical_report(
        first_bound,
        report_state=_state(raw_not_applicable=True, accepted=False),
        runtime_metadata={"execution_id": "run_parity"},
    )
    first_report = DeterministicFinalReportRenderer().render(
        {"runtime_status": "completed", "ENGINEERING_CONCLUSION": first_bound},
        runtime_metadata={"execution_id": "run_parity"},
    )
    second_report = DeterministicFinalReportRenderer().render(
        {"runtime_status": "completed", "ENGINEERING_CONCLUSION": second_bound},
        runtime_metadata={"execution_id": "run_parity"},
    )

    assert engineering_conclusion_integrity_evaluator.stable_payload(first_read) == (
        engineering_conclusion_integrity_evaluator.stable_payload(second_read)
    )
    assert engineering_conclusion_integrity_evaluator.stable_payload(first_bound) == (
        engineering_conclusion_integrity_evaluator.stable_payload(second_bound)
    )
    assert "Substantive Conclusion State: NOT_APPLICABLE" in first_report
    assert "Emission Integrity: EMISSION_VERIFIED" in first_report
    assert (
        "Emission Integrity Reason: authoritative_and_emitted_payloads_match"
        in first_report
    )
    assert "Emission Conflict Count: 0" in first_report
    assert "Authoritative Fingerprint:" in first_report
    assert "Emitted Fingerprint:" in first_report
    assert "Next Gate: none" in second_report


def test_human_report_projection_does_not_repair_failed_emission():
    conclusion = _conclusion()
    emitted = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    emitted["next_gate"] = "foreign_gate"
    failed = engineering_conclusion_integrity_evaluator.evaluate_emission_integrity(
        conclusion,
        emitted,
    )
    bound = engineering_conclusion_integrity_evaluator.bind_to_canonical_report(
        {
            **conclusion,
            "emission_integrity": failed["emission_integrity"],
            "emission_integrity_reason": failed["emission_integrity_reason"],
            "emission_conflict_count": failed["emission_conflict_count"],
            "emission_conflict_fields": failed["emission_conflict_fields"],
            "authoritative_fingerprint": failed["authoritative_fingerprint"],
            "emitted_fingerprint": failed["emitted_fingerprint"],
            "authoritative_emitted_stable_field_comparison": (
                failed["authoritative_emitted_stable_field_comparison"]
            ),
        },
        report_state=_state(),
        runtime_metadata={"execution_id": "run_parity"},
    )

    report = DeterministicFinalReportRenderer().render(
        {"runtime_status": "completed", "ENGINEERING_CONCLUSION": bound},
        runtime_metadata={"execution_id": "run_parity"},
    )

    assert failed["emission_integrity"] == "EMISSION_FAILED"
    assert "next_gate" in failed["emission_conflict_fields"]
    assert "Emission Integrity: EMISSION_FAILED" in report
    assert "Emission Conflict Fields: next_gate" in report
    assert "Next Gate: continue_with_next_governed_runtime_stage" in report


def test_deliberate_conflict_visible_and_renderer_does_not_repair():
    conclusion = engineering_conclusion_integrity_evaluator.normalize({
        "conclusion_state": "NOT_APPLICABLE",
        "failure_reason": "none",
        "root_cause": "RAW_RESULT_NOT_APPLICABLE",
        "next_gate": "repair_raw_validation_result_identity",
        "recommended_action": "repair_raw_validation_result_identity",
    })

    report = DeterministicFinalReportRenderer().render(
        {"runtime_status": "completed", "ENGINEERING_CONCLUSION": conclusion},
        runtime_metadata={"execution_id": "run_conflict"},
    )

    assert conclusion["engineering_conclusion_integrity_state"] == (
        "ENGINEERING_CONCLUSION_CONFLICT"
    )
    assert "not_applicable_raw_result_identity_repair_gate_incompatible" in report
    assert "Next Gate: repair_raw_validation_result_identity" in report


def test_parity_evaluation_does_not_change_substantive_semantics(tmp_path):
    conclusion = _conclusion(raw_not_applicable=True, accepted=False)
    before = engineering_conclusion_integrity_evaluator.stable_payload(conclusion)
    artifact = tmp_path / "conclusion.json"
    engineering_conclusion_integrity_evaluator.persist_conclusion(conclusion, artifact)
    readback = engineering_conclusion_integrity_evaluator.read_persisted_conclusion(
        artifact,
    )
    emission = engineering_conclusion_integrity_evaluator.structured_emission_payload(
        conclusion,
    )
    engineering_conclusion_integrity_evaluator.persistence_emission_parity(
        readback,
        emission,
    )
    after = engineering_conclusion_integrity_evaluator.stable_payload(conclusion)

    assert before == after
    assert before["next_gate"] == "none"
    assert set(STABLE_SEMANTIC_FIELDS).issubset(before.keys())
