import io
import hashlib
import json

from runtime.reporting.final_report_renderer import (
    REPORT_BEGIN_MARKER,
    REPORT_END_MARKER,
    DeterministicFinalReportRenderer,
    HUMAN_REPORT_MEASUREMENT_CONTRACT,
)


def _state():
    return {
        "runtime_status": "completed",
        "training_batch_size": 3,
        "warning_count": 0,
        "error_count": 0,
        "report_timing_status": "VALID",
        "report_timing_semantics_valid": False,
        "execution_invoked": False,
        "execution_started": True,
        "execution_completed": True,
        "runner_invoked": False,
        "runner_status": "COMPLETED",
        "operation": "replace_color",
        "leading_candidate": {
            "candidate_id": "semantic_to_transformation_compiler_0",
            "source": "semantic_compiler",
            "operation": "replace_color",
            "entered_arena": True,
        },
        "COGNITIVE_SEARCH_REPORT": {
            "overall_search_quality": 0.4022,
            "search_efficiency": 0.0138,
            "search_coverage": 1.0,
            "average_route_quality": 0.0515,
        },
        "COGNITIVE_CANDIDATE_ARENA_REPORT": {
            "validation_probe_outcome": "ACCEPTED",
            "arena_decision": "TIE_CONFIRMED",
            "winner_selected": False,
        },
        "EVIDENCE_GENERATION_REPORT": {
            "existing_evidence_plan_reused": True,
            "scheduled_validation_task": "elite_validation_task_31",
        },
        "VALIDATION_TASK_EXECUTION_REPORT": {
            "execution_admission": "ADMITTED",
            "execution_state": "RAW_RESULT_CAPTURED",
            "raw_validation_result_id": "raw_validation_result_e8d6e6cad0fb",
            "target_reference_forwarded_to_solver": False,
        },
        "VALIDATION_EVIDENCE_EVALUATION_REPORT": {
            "evidence_evaluation_state": "BLOCKED_MISSING_EVALUATION_CONTRACT",
        },
        "ARENA_EVIDENCE_ADMISSION_REPORT": {
            "arena_reentry": False,
        },
        "performance_report": {
            "total_runtime_seconds": 37.3507,
            "active_compute_time_seconds": 74.2421,
            "timing_coverage": 1.0,
            "untracked_runtime_seconds": 0,
            "report_lifecycle_time": 0.1158,
            "performance_action": "profile_training_signal_loading_and_cache_reuse",
            "governance_budget_exceeded": False,
            "stage_metrics": [
                {
                    "stage_name": "Task Selection",
                    "exclusive_duration_seconds": 9.2036,
                }
            ],
        },
        "ENGINEERING_CONCLUSION": {
            "largest_success": "scheduled validation task executed and raw result captured",
            "largest_regression": "none",
            "current_open_decision": "WAITING_RAW_RESULT_EVIDENCE_EVALUATION",
            "next_decision_gate": "evaluate_raw_validation_result",
            "current_bottleneck": "validation_evidence_evaluation",
            "root_cause": "raw_validation_result_not_yet_evaluated",
            "responsible_component": "VALIDATION_EVIDENCE_EVALUATOR",
            "immediate_next_development_task": "evaluate_raw_validation_result_without_truth_grant",
            "engineering_priority": "HIGH",
        },
        "machine_only_bulk": [
            {
                "field": "Not Available",
                "enabled": False,
                "fingerprint": f"fingerprint_{index}",
            }
            for index in range(2000)
        ],
        "CRITICAL_EXECUTION_TRACE": "\n".join(
            f"BY_PROPOSAL_RUNTIME_INTERNAL_FIELD_{index}"
            for index in range(2000)
        ),
    }


def _metadata():
    return {
        "execution_id": "run_20260804_012546",
        "timestamp": "2026-08-04 01:26:36",
        "mode": "adaptive",
        "report_level": "normal",
        "runtime_status": "COMPLETED",
        "training_batch_size": 3,
        "warning_count": 0,
        "error_count": 0,
    }


def test_human_report_ignores_old_character_budget_and_preserves_prefix():
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)
    report = renderer.render(_state(), runtime_metadata=_metadata())
    metrics = renderer.report()

    assert report.startswith(REPORT_BEGIN_MARKER)
    assert report.rstrip().endswith(REPORT_END_MARKER)
    assert report.count(REPORT_BEGIN_MARKER) == 1
    assert report.count(REPORT_END_MARKER) == 1
    assert "NEXRYN HUMAN RUN SUMMARY" in report
    assert "REPORT INTEGRITY" in report
    assert "Console Appendix: omitted" not in report
    assert "Report Integrity: TRUNCATED" not in report
    assert metrics["human_report_character_limit"] == "NONE"
    assert metrics["human_report_truncation_enabled"] is False
    assert metrics["human_report_truncated"] is False
    assert metrics["deprecated_console_budget_applied_to_human_report"] is False


def test_human_report_excludes_machine_bulk_and_trace():
    report = DeterministicFinalReportRenderer().render(
        _state(),
        runtime_metadata=_metadata(),
    )

    assert "machine_only_bulk" not in report
    assert "CRITICAL EXECUTION TRACE" not in report
    assert "BY_PROPOSAL_RUNTIME_INTERNAL_FIELD_1999" not in report
    assert "Not Available" not in report
    assert "Human Report Canonical Binding Integrity: COMPLETE" in report
    assert "Human Report Semantic Completeness: COMPLETE" in report
    assert "Human Report Generic Unavailable Value Count: 0" in report


def test_human_report_uses_conclusion_run_id_as_explicit_compatibility_fallback():
    state = _state()
    state["ENGINEERING_CONCLUSION"]["conclusion_run_id"] = "run_20260805_005212"
    metadata = _metadata()
    metadata.pop("execution_id")

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=metadata,
    )

    assert "Run Id: run_20260805_005212" in report
    assert "Human Report Canonical Binding Integrity: COMPLETE" in report


def test_human_report_detects_canonical_source_conflict():
    state = _state()
    state["run_id"] = "run_conflicting_state"

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Run Id: Canonical source conflict" in report
    assert "Human Report Canonical Binding Integrity: CONFLICTED" in report
    assert "Human Report Semantic Completeness: INCOMPLETE" in report
    assert "Human Report Binding Conflict Count: 1" in report


def test_human_report_preserves_false_and_zero_values_as_bound_values():
    report = DeterministicFinalReportRenderer().render(
        _state(),
        runtime_metadata=_metadata(),
    )

    assert "Warnings: 0" in report
    assert "Errors: 0" in report
    assert "Untracked Time: 0 s" in report
    assert "Winner Selected: FALSE" in report
    assert "Target Reference Forwarded To Solver: FALSE" in report


def test_raw_result_captured_without_raw_result_id_fails_identity_closed():
    state = _state()
    state["VALIDATION_TASK_EXECUTION_REPORT"].pop("raw_validation_result_id")

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Raw Result State: RAW_RESULT_ENVELOPE_INCOMPLETE" in report
    assert "Raw Validation Result Id: RAW_VALIDATION_RESULT_ID_NOT_ISSUED" in report
    assert "Human Report Canonical Binding Integrity: COMPLETE" in report
    assert "Human Report Expected Missing Count: 0" in report
    assert "Expected artifact missing" not in report


def test_conclusion_task_id_is_not_used_as_relevant_candidate():
    state = _state()
    state.pop("leading_candidate")
    state["ENGINEERING_CONCLUSION"]["conclusion_task_id"] = "elite_validation_task_31"

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Relevant Candidate: elite_validation_task_31" not in report


def test_unbound_raw_validation_result_does_not_recommend_evaluation():
    state = _state()
    state.pop("ENGINEERING_CONCLUSION")
    state["VALIDATION_TASK_EXECUTION_REPORT"] = {
        "execution_admission": "ADMITTED",
        "execution_state": "RAW_RESULT_CAPTURED",
        "raw_validation_result_id": None,
        "raw_result_captured": True,
        "RAW_VALIDATION_RESULT_ENVELOPE": {
            "raw_validation_result_schema_version": "1.0",
            "raw_validation_result_id": None,
            "raw_validation_result_state": "RAW_RESULT_CAPTURED",
            "run_id": None,
            "task_id": "task-localized-remap",
            "execution_plan_id": "evidence_plan_1",
            "executor_invocation_id": "validation_execution_1",
            "validation_attempt_id": "validation_attempt_1",
            "artifact_state": "ARTIFACT_CAPTURED",
            "payload_state": "PAYLOAD_CAPTURED",
            "provenance_state": "RAW_RESULT_PROVENANCE_UNBOUND",
            "binding_integrity_state": "CONFLICTED",
            "binding_conflict_count": 5,
            "downstream_structural_eligibility": "STRUCTURALLY_INELIGIBLE",
            "structural_ineligibility_reason": "RAW_VALIDATION_IDENTITY_INPUT_UNAVAILABLE",
            "producer_component_id": "semantic_to_transformation_compiler_0",
            "producer_source_type": "semantic_compiler_candidate_source",
        },
    }

    report = DeterministicFinalReportRenderer().render(
        state,
        runtime_metadata=_metadata(),
    )

    assert "Raw Validation Result Id: RAW_VALIDATION_RESULT_ID_NOT_ISSUED" in report
    assert "Immediate Next Development Task: evaluate_raw_validation_result_without_truth_grant" not in report


def test_human_report_exposes_observability_contradictions_with_zero_warnings():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(_state(), runtime_metadata=_metadata())

    assert "Report Timing Status is VALID" in report
    assert "Execution Invoked is FALSE" in report
    assert "Runner Invoked is FALSE" in report
    assert "Warning Count is zero" in report
    assert renderer.report()["human_report_critical_observability_note_count"] == 4


def test_persistence_and_emission_preserve_complete_human_report(tmp_path):
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)
    report = renderer.render(
        _state(),
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )
    artifact = (tmp_path / "runtime_report.txt").read_text(encoding="utf-8")
    stream = io.StringIO()

    renderer.emit(report, stream=stream)

    assert artifact == report
    assert stream.getvalue().rstrip("\n") == report.rstrip("\n")
    assert renderer.report()["human_report_persistence_matches_emission"] is True
    assert renderer.report()["human_report_persisted_artifact_byte_count"] == len(report.encode("utf-8"))
    assert renderer.report()["human_report_emitted_payload_byte_count"] == len(stream.getvalue().encode("utf-8"))


def test_missing_or_duplicate_boundaries_prevent_complete_integrity():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(_state(), runtime_metadata=_metadata())

    assert "missing_report_begin_marker" in renderer.validate(
        report.replace(REPORT_BEGIN_MARKER, "", 1)
    )
    assert "missing_report_end_marker" in renderer.validate(
        report.replace(REPORT_END_MARKER, "", 1)
    )
    assert "report_begin_marker_count_not_one" in renderer.validate(
        report.replace(REPORT_BEGIN_MARKER, REPORT_BEGIN_MARKER + "\n" + REPORT_BEGIN_MARKER, 1)
    )


def test_old_environment_limit_cannot_reactivate_human_report_truncation(monkeypatch):
    monkeypatch.setenv("NEXRYN_HUMAN_REPORT_MAX_CHARS", "200")
    report = DeterministicFinalReportRenderer(console_budget_chars=200).render(
        _state(),
        runtime_metadata=_metadata(),
    )

    assert report.startswith(REPORT_BEGIN_MARKER)
    assert "NEXRYN HUMAN RUN SUMMARY" in report
    assert "REPORT INTEGRITY" in report
    assert report.rstrip().endswith(REPORT_END_MARKER)


def test_former_tail_retention_boundary_does_not_remove_human_report_prefix():
    state = _state()
    state["machine_only_bulk"].extend(
        {
            "field": "Not Available",
            "enabled": False,
            "diagnostic_payload": "BY_PROPOSAL_RUNTIME" * 200,
        }
        for _ in range(250)
    )

    report = DeterministicFinalReportRenderer(console_budget_chars=32_000).render(
        state,
        runtime_metadata=_metadata(),
    )

    assert len(report) < 32_000
    assert report.startswith(REPORT_BEGIN_MARKER)
    assert "\nNEXRYN HUMAN RUN SUMMARY\n" in report
    assert "BY_PROPOSAL_RUNTIME" not in report
    assert report.rstrip().endswith(REPORT_END_MARKER)
    assert "Human Report Integrity State: COMPLETE" in report


def test_deprecated_budget_summary_path_returns_complete_report_without_truncation():
    renderer = DeterministicFinalReportRenderer(console_budget_chars=10)
    report = renderer.render(_state(), runtime_metadata=_metadata())
    canonical = {"report_level": "normal"}

    legacy_result = renderer._render_budget_summary(canonical, report)

    assert legacy_result == report
    assert "TRUNCATED" not in legacy_result
    assert legacy_result.startswith(REPORT_BEGIN_MARKER)
    assert legacy_result.rstrip().endswith(REPORT_END_MARKER)


def test_measurement_contract_is_explicit_and_rendered_concisely():
    report = DeterministicFinalReportRenderer().render(
        _state(),
        runtime_metadata=_metadata(),
    )

    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["schema_version"] == "1.0"
    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["canonical_encoding"] == "UTF-8"
    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["canonical_line_ending"] == "LF"
    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["unicode_normalization"] == "NFC"
    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["character_count_unit"] == "UNICODE_CODE_POINTS"
    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["byte_count_unit"] == "UTF8_OCTETS"
    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["trailing_newline_policy"] == "INCLUDED_EXACTLY_ONCE"
    assert HUMAN_REPORT_MEASUREMENT_CONTRACT["fingerprint_algorithm"] == "SHA-256"
    assert "Human Report Measurement Contract Version: 1.0" in report
    assert "Canonical Line Ending: LF" in report
    assert "Canonical Encoding: UTF-8" in report
    assert "Detached Emission Receipt: PENDING" in report


def test_canonical_body_measurement_is_reproducible_and_non_self_referential():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(_state(), runtime_metadata=_metadata())
    measurement = renderer.report()
    canonical_body = renderer._canonical_body_text(report)
    expected_fingerprint = hashlib.sha256(canonical_body.encode("utf-8")).hexdigest()

    assert measurement["human_report_canonical_body_fingerprint"] == expected_fingerprint
    assert measurement["human_report_canonical_body_character_count"] == len(canonical_body)
    assert measurement["human_report_canonical_body_byte_count"] == len(canonical_body.encode("utf-8"))
    mutated = report.replace(
        "Canonical Body Fingerprint: " + expected_fingerprint,
        "Canonical Body Fingerprint: " + "0" * 64,
    )
    assert renderer._canonical_body_text(mutated) == canonical_body
    semantic_mutation = report.replace("Run Id: run_20260804_012546", "Run Id: run_changed")
    assert renderer._canonical_body_text(semantic_mutation) != canonical_body


def test_canonical_measurement_normalizes_crlf_and_preserves_utf8_byte_difference():
    renderer = DeterministicFinalReportRenderer()
    text = f"{REPORT_BEGIN_MARKER}\r\nCafé\r\n{REPORT_END_MARKER}\r\n"
    canonical = renderer._canonical_measurement_text(text)
    measurement = renderer._measure_text_scope(canonical, scope="test")

    assert "\r" not in canonical
    assert canonical.endswith("\n")
    assert measurement["character_count"] == len(canonical)
    assert measurement["byte_count"] == len(canonical.encode("utf-8"))
    assert measurement["byte_count"] > measurement["character_count"]


def test_persisted_artifact_is_remeasured_from_exact_bytes_and_receipt_is_detached(tmp_path):
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _state(),
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )
    artifact_path = tmp_path / "runtime_report.txt"
    payload = artifact_path.read_bytes()

    assert renderer.report()["human_report_persistence_integrity"] == "VERIFIED"
    assert renderer.report()["human_report_persisted_artifact_byte_count"] == len(payload)
    assert renderer.report()["human_report_persisted_artifact_fingerprint"] == hashlib.sha256(payload).hexdigest()
    assert renderer.report()["human_report_persisted_artifact_readback_performed"] is True
    assert b"receipt_schema_version" not in payload
    assert "Detached Emission Receipt: PENDING" in report


def test_emission_receipt_is_created_after_emit_and_measured_independently(tmp_path):
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _state(),
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )
    stream = io.StringIO()

    renderer.emit(report, stream=stream)
    metrics = renderer.report()
    emitted_payload = stream.getvalue().encode("utf-8")

    assert metrics["human_report_emission_integrity"] == "VERIFIED"
    assert metrics["human_report_emitted_payload_byte_count"] == len(emitted_payload)
    assert metrics["human_report_emitted_payload_fingerprint"] == hashlib.sha256(emitted_payload).hexdigest()
    assert metrics["human_report_persistence_emission_equivalence"] == "MATCHED"
    assert metrics["human_report_receipt_integrity"] == "VERIFIED"
    receipt = metrics["human_report_detached_receipt"]
    assert receipt["receipt_scope"] == "DETACHED_OUTSIDE_HUMAN_REPORT_ENVELOPE"
    assert receipt["receipt_created_after_emission"] is True
    assert receipt["emitted_payload"]["fingerprint"] != ""
    receipt_path = tmp_path / "runtime_report.txt.receipt.json"
    assert receipt_path.exists()
    stored = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert stored["receipt_schema_version"] == "1.0"


def test_report_mutation_invalidates_detached_receipt(tmp_path):
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _state(),
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )
    renderer.emit(report, stream=io.StringIO())
    receipt = renderer.report()["human_report_detached_receipt"]
    artifact_path = tmp_path / "runtime_report.txt"

    assert renderer.verify_detached_receipt(receipt, artifact_path=artifact_path)["persisted_artifact_integrity"] == "VERIFIED"
    artifact_path.write_text(report + "mutation\n", encoding="utf-8", newline="\n")

    verification = renderer.verify_detached_receipt(receipt, artifact_path=artifact_path)

    assert verification["persisted_artifact_integrity"] == "FAILED"
    assert verification["receipt_integrity"] == "FAILED"


def test_emission_not_attempted_is_not_verified():
    renderer = DeterministicFinalReportRenderer()
    renderer.render(_state(), runtime_metadata=_metadata())
    metrics = renderer.report()

    assert metrics["human_report_emission_integrity"] == "NOT_VERIFIED"
    assert metrics["human_report_receipt_integrity"] == "NOT_AVAILABLE"
    assert metrics["human_report_persistence_emission_equivalence"] == "NOT_VERIFIED"


def test_legacy_attestation_fixture_is_not_reinterpreted_as_verified():
    legacy = "\n".join([
        REPORT_BEGIN_MARKER,
        "Persisted Character Count: 5030",
        "Emitted Character Count: 5030",
        "Persisted Fingerprint: 6d68abcd",
        "Emitted Fingerprint: 6d68abcd",
        REPORT_END_MARKER,
        "",
    ])
    renderer = DeterministicFinalReportRenderer()
    lf = renderer._canonical_measurement_text(legacy)
    crlf_bytes = lf.replace("\n", "\r\n").encode("utf-8")
    lf_bytes = lf.encode("utf-8")

    assert hashlib.sha256(crlf_bytes).hexdigest() != hashlib.sha256(lf_bytes).hexdigest()
    assert not hashlib.sha256(lf_bytes).hexdigest().startswith("6d68")
    assert renderer._measure_text_scope(legacy, scope="legacy")["fingerprint"] == hashlib.sha256(lf_bytes).hexdigest()
