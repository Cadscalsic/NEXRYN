from runtime.reporting.report_level_separation_contract import (
    FieldPolicy,
    FieldPriority,
    ReportLevel,
    ReportLevelSeparationContract,
    VISIBILITY_POLICY_VERSION,
)


def _canonical_report():
    return {
        "runtime_status": "completed",
        "final_status": "completed",
        "total_runtime_seconds": 4.2,
        "execution_time": 4.2,
        "execution_coverage": 1.0,
        "snapshot_coverage": 1.0,
        "lifecycle_coverage": 1.0,
        "generated_concepts": 5,
        "generated_programs": 3,
        "validated_programs": 2,
        "truth_candidate_count": 1,
        "overall_search_quality": 0.78,
        "average_program_confidence": 0.84,
        "system_health": "healthy",
        "critical_warnings": [],
        "critical_errors": [],
        "execution_summary": {"total": 1},
        "cognitive_outputs": {"concepts": 5},
        "program_quality": {"average_program_confidence": 0.84},
        "search_quality": {"overall_search_quality": 0.78},
        "knowledge_pipeline_summary": {"fabric_links": 2},
        "timing_summary": {"total_runtime_seconds": 4.2},
        "coverage_metrics": {"execution_coverage": 1.0},
        "warnings": ["normal warning"],
        "errors": ["normal error"],
        "execution_tree": {"root": {"children": []}},
        "runtime_telemetry": {"raw": True},
        "execution_telemetry": {"events": []},
        "metric_ownership_map": {"metric": "owner"},
        "snapshot_payloads": [{"payload": "large"}],
        "validation_history": [{"status": "passed"}],
        "snapshot_summaries": {"snapshot_count": 1},
        "validation_diagnostics": {"checks": 3},
        "metric_attribution_diagnostics": {"owners": 1},
        "execution_registry_diagnostics": {"instances": 1},
    }


def test_minimal_report_validation_removes_diagnostic_only_fields():
    contract = ReportLevelSeparationContract()
    result = contract.apply_visibility(_canonical_report(), level="minimal")
    visible = result["visible_report"]
    metadata = result["report_level_metadata"]

    assert visible["runtime_status"] == "completed"
    assert visible["generated_concepts"] == 5
    assert "execution_tree" not in visible
    assert "runtime_telemetry" not in visible
    assert "snapshot_payloads" not in visible
    assert metadata["report_level"] == "MINIMAL"
    assert metadata["diagnostic_fields_removed"] > 0
    assert metadata["technical_appendix_available"] is True
    assert metadata["report_validation_success"] is True


def test_normal_report_validation_excludes_raw_diagnostics():
    contract = ReportLevelSeparationContract()
    result = contract.apply_visibility(_canonical_report(), level="normal")
    visible = result["visible_report"]

    assert "execution_summary" in visible
    assert "program_quality" in visible
    assert "knowledge_pipeline_summary" in visible
    assert "runtime_telemetry" not in visible
    assert "metric_ownership_map" not in visible
    assert "snapshot_payloads" not in visible
    validation = contract.validate(
        visible,
        level="normal",
        canonical_report=_canonical_report(),
    )
    assert validation["report_validation_success"] is True


def test_diagnostic_report_validation_allows_deep_visibility():
    contract = ReportLevelSeparationContract()
    result = contract.apply_visibility(_canonical_report(), level="diagnostic")
    visible = result["visible_report"]

    assert "execution_tree" in visible
    assert "runtime_telemetry" in visible
    assert "snapshot_summaries" in visible
    assert "metric_attribution_diagnostics" in visible
    assert result["report_level_metadata"]["report_validation_success"] is True


def test_forbidden_field_validation_detects_diagnostic_pollution():
    contract = ReportLevelSeparationContract()
    report = {
        "runtime_status": "completed",
        "final_status": "completed",
        "total_runtime_seconds": 1.0,
        "execution_coverage": 1.0,
        "snapshot_coverage": 1.0,
        "generated_concepts": 1,
        "generated_programs": 1,
        "validated_programs": 1,
        "truth_candidate_count": 0,
        "overall_search_quality": 0.5,
        "average_program_confidence": 0.5,
        "system_health": "healthy",
        "execution_tree": {},
    }

    validation = contract.validate(report, level="minimal")

    assert "execution_tree" in validation["forbidden_fields"]
    assert "forbidden_field:execution_tree" in validation["validation_errors"]
    assert validation["report_validation_success"] is False


def test_required_field_validation_detects_missing_fields():
    validation = ReportLevelSeparationContract().validate(
        {"runtime_status": "completed"},
        level="normal",
    )

    assert "execution_summary" in validation["missing_required_fields"]
    assert any(
        error.startswith("missing_required_field:")
        for error in validation["validation_errors"]
    )


def test_externalized_field_validation_and_policy_lookup():
    contract = ReportLevelSeparationContract()
    result = contract.apply_visibility(_canonical_report(), level="normal")

    assert "snapshot_payloads" in result["externalized_fields"]
    policy = contract.visibility_for("metric_ownership_map")
    assert policy["diagnostic_only"] is True
    assert policy["externalizable"] is True
    assert policy["field_priority"] == "DIAGNOSTIC_ONLY"


def test_visibility_conflicts_are_detected():
    contract = ReportLevelSeparationContract()
    contract.field_policies["bad_duplicate"] = FieldPolicy(
        field_name="bad_duplicate",
        report_level_visibility=(ReportLevel.MINIMAL, ReportLevel.MINIMAL),
        field_priority=FieldPriority.LOW,
        field_owner="test",
        field_type="test",
    )
    contract.field_policies["bad_diagnostic"] = FieldPolicy(
        field_name="bad_diagnostic",
        report_level_visibility=(ReportLevel.MINIMAL,),
        field_priority=FieldPriority.DIAGNOSTIC_ONLY,
        field_owner="test",
        field_type="test",
        diagnostic_only=True,
    )
    contract.field_policies["bad_externalized"] = FieldPolicy(
        field_name="bad_externalized",
        report_level_visibility=(ReportLevel.NORMAL,),
        field_priority=FieldPriority.LOW,
        field_owner="test",
        field_type="test",
        externalizable=True,
    )

    errors = contract.validate_policy_registry()

    assert "duplicate_field_visibility:bad_duplicate" in errors
    assert "visibility_conflict:bad_diagnostic" in errors
    assert "externalization_conflict:bad_externalized" in errors


def test_priority_assignment_and_owners_are_explicit():
    contract = ReportLevelSeparationContract()

    for policy in contract.field_policies.values():
        assert policy.field_priority in FieldPriority
        assert policy.field_owner
        assert policy.field_type

    assert (
        contract.policy_for("runtime_status").field_priority
        == FieldPriority.CRITICAL
    )
    assert (
        contract.policy_for("average_program_confidence").field_priority
        == FieldPriority.HIGH
    )
    assert (
        contract.policy_for("snapshot_payloads").field_priority
        == FieldPriority.DIAGNOSTIC_ONLY
    )


def test_visibility_metadata_generation_is_complete():
    contract = ReportLevelSeparationContract()
    result = contract.apply_visibility(_canonical_report(), level="normal")
    metadata = result["report_level_metadata"]

    assert metadata["report_level"] == "NORMAL"
    assert metadata["visible_section_count"] > 0
    assert metadata["hidden_section_count"] > 0
    assert metadata["externalized_section_count"] > 0
    assert metadata["report_validation_success"] is True
    assert metadata["visibility_policy_version"] == VISIBILITY_POLICY_VERSION


def test_deterministic_field_visibility():
    contract = ReportLevelSeparationContract()

    first = contract.apply_visibility(_canonical_report(), level="normal")
    second = contract.apply_visibility(_canonical_report(), level="normal")

    assert list(first["visible_report"].keys()) == list(
        second["visible_report"].keys(),
    )
    assert first["report_level_metadata"] == second["report_level_metadata"]


def test_section_visibility_examples():
    contract = ReportLevelSeparationContract()

    assert contract.section_visibility_for("Execution Summary")[
        "report_level_visibility"
    ] == ["MINIMAL", "NORMAL", "DIAGNOSTIC"]
    assert contract.section_visibility_for("Execution Tree")[
        "report_level_visibility"
    ] == ["DIAGNOSTIC"]
    assert contract.section_visibility_for("Snapshot Payloads")[
        "externalizable"
    ] is True
