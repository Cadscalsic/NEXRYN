from runtime.reporting.final_report_renderer import (
    REPORT_BEGIN_MARKER,
    REPORT_END_MARKER,
    SECTION_ORDER,
    DeterministicFinalReportRenderer,
)


def _report_state():
    return {
        "runtime_status": "completed",
        "tasks_executed": 3,
        "successful_tasks": 3,
        "generated_concepts": 4,
        "generated_programs": 2,
        "truth_candidate_count": 1,
        "PROGRAM_SYNTHESIS_REPORT": {
            "average_program_confidence": 0.82,
            "highest_confidence": 0.91,
            "lowest_confidence": 0.64,
            "validation_distribution": {"VALID": 2},
        },
        "COGNITIVE_SEARCH_REPORT": {
            "overall_search_quality": 0.76,
            "search_efficiency": 0.81,
            "search_coverage": 0.69,
            "search_entropy": 0.33,
            "average_route_quality": 0.71,
            "route_count": 3,
        },
        "RUNTIME_LIFECYCLE_REPORT": {
            "total_executions": 3,
            "completed_executions": 3,
            "archived_executions": 3,
            "execution_coverage": 1.0,
            "snapshot_coverage": 1.0,
            "lifecycle_coverage": 1.0,
        },
        "EXECUTION_BINDING_REPORT": {
            "binding_status": "BOUND",
            "missing_execution_instances": 0,
            "missing_snapshot_runtimes": 0,
        },
        "RUNTIME_METRIC_SYNCHRONIZATION_REPORT": {
            "metric_validation_status": "VALID",
        },
        "RUNTIME_OBSERVABILITY_REPORT": {
            "observability_status": "HEALTHY",
        },
        "execution_timing": {
            "execution_timing_state": {
                "total_wall_time": 10.0,
                "cognitive_runtime_time": 6.0,
                "unattributed_time": 0.5,
                "timing_coverage": 0.95,
                "report_generation_time": 0.2,
                "finalization_time": 0.3,
            },
            "timing_records": [
                {
                    "timing_scope": "BOOT_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.5,
                    "inclusive_duration_seconds": 0.5,
                    "exclusive_duration_seconds": 0.5,
                    "cpu_duration_seconds": 0.0,
                    "measurement_source": "execution_timing_unification_engine",
                    "measurement_method": "external_scope_duration_or_zero_when_unobserved",
                },
                {
                    "timing_scope": "REPORT_GENERATION_TIME",
                    "timing_status": "OBSERVED",
                    "validation_status": "VALID",
                    "wall_duration_seconds": 0.2,
                    "inclusive_duration_seconds": 0.2,
                    "exclusive_duration_seconds": 0.2,
                    "cpu_duration_seconds": 0.0,
                    "measurement_source": "execution_timing_unification_engine",
                    "measurement_method": "external_scope_duration_or_zero_when_unobserved",
                },
            ],
        },
        "performance_report": {
            "total_runtime_seconds": 10.0,
            "active_compute_time_seconds": 8.0,
            "untracked_runtime_seconds": 0.5,
            "stage_metrics": [
                {
                    "stage_name": "grid_analysis",
                    "total_duration": 1.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "reasoning",
                    "total_duration": 3.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "search",
                    "total_duration": 2.0,
                    "execution_count": 1,
                },
                {
                    "stage_name": "evaluation",
                    "total_duration": 0.4,
                    "execution_count": 1,
                },
            ],
        },
        "compact_report": {
            "heavy_keys_removed": 1,
            "arrays_summarized": 1,
            "repeated_reports_collapsed": 1,
        },
        "raw_nested_report": {"nested": {"not": "printed"}},
    }


def _metadata():
    return {
        "system": "NEXRYN",
        "mode": "test",
        "profile": "unit",
        "report_level": "normal",
        "execution_id": "exec-1",
        "timestamp": "2026-07-15T00:00:00Z",
        "runtime_status": "completed",
        "execution_time": 1.25,
    }


def test_render_has_boundaries_and_stable_section_order():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert report.startswith(REPORT_BEGIN_MARKER)
    assert report.rstrip().endswith(REPORT_END_MARKER)
    positions = [report.index(section) for section in SECTION_ORDER]
    assert positions == sorted(positions)
    assert renderer.report()["report_complete"] is True


def test_render_has_single_final_status_and_no_raw_dict_repr():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
    )

    assert report.count("NEXRYN :: FINAL STATUS") == 1
    assert "{'nested'" not in report
    assert "raw_nested_report" not in report


def test_render_does_not_begin_or_end_with_partial_structure():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
    )

    first_after_marker = report[len(REPORT_BEGIN_MARKER):].lstrip()
    assert first_after_marker.startswith("=")
    assert not report.rstrip().endswith(("{", "[", ":", ","))


def test_identical_inputs_render_identically():
    renderer = DeterministicFinalReportRenderer()

    first = renderer.render(_report_state(), runtime_metadata=_metadata())
    second = renderer.render(_report_state(), runtime_metadata=_metadata())

    assert first == second


def test_console_budget_fallback_remains_complete():
    state = _report_state()
    state["huge_diagnostic"] = "x" * 5000
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)

    report = renderer.render(state, runtime_metadata=_metadata())

    assert report.startswith(REPORT_BEGIN_MARKER)
    assert report.rstrip().endswith(REPORT_END_MARKER)
    assert "Console Appendix: omitted" in report
    assert renderer.report()["report_truncated"] is True
    assert renderer.report()["report_complete"] is True


def test_console_budget_writes_full_text_artifact(tmp_path):
    state = _report_state()
    state["huge_diagnostic"] = "x" * 5000
    renderer = DeterministicFinalReportRenderer(console_budget_chars=200)

    console_report = renderer.render(
        state,
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )

    artifact_text = (tmp_path / "runtime_report.txt").read_text(
        encoding="utf-8",
    )
    assert "Console Appendix: omitted" in console_report
    assert "Console Appendix: omitted" not in artifact_text
    assert artifact_text.startswith(REPORT_BEGIN_MARKER)
    assert artifact_text.rstrip().endswith(REPORT_END_MARKER)


def test_text_artifact_matches_rendered_report(tmp_path):
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(
        _report_state(),
        runtime_metadata=_metadata(),
        artifact_directory=tmp_path,
        write_artifact=True,
    )

    artifact = tmp_path / "runtime_report.txt"
    assert artifact.read_text(encoding="utf-8") == report
    assert renderer.report()["report_artifact_written"] is True


def test_duplicate_section_detection():
    renderer = DeterministicFinalReportRenderer()
    report = renderer.render(_report_state(), runtime_metadata=_metadata())
    invalid_report = report.replace(
        "FINAL STATUS",
        "FINAL STATUS\nFINAL STATUS",
        1,
    )

    errors = renderer.validate(invalid_report)

    assert "duplicate_section:FINAL STATUS" in errors


def test_normal_report_restores_per_stage_timing_visibility():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="normal",
    )

    assert "COGNITIVE STAGE TIMING" in report
    assert "stage_name" in report
    assert "Reasoning" in report
    assert "Search" in report
    assert "Grid Analysis" in report
    assert "percentage_of_total_runtime" in report
    assert "Top Three Time Consumers" in report
    assert "Total Wall Time: 10 s" in report
    assert "Active Compute Time: 8 s" in report
    assert "Untracked Time: 0.5 s" in report


def test_minimal_report_keeps_top_timing_summary_without_full_stage_table():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="minimal",
    )

    assert "TIMING SUMMARY" in report
    assert "Total Wall Time: 10 s" in report
    assert "Active Compute Time: 8 s" in report
    assert "Top Three Time Consumers" in report
    assert "COGNITIVE STAGE TIMING" not in report


def test_diagnostic_report_exposes_timing_detail_fields():
    report = DeterministicFinalReportRenderer().render(
        _report_state(),
        runtime_metadata=_metadata(),
        report_level="diagnostic",
    )

    assert "DIAGNOSTIC TIMING DETAIL" in report
    assert "inclusive=" in report
    assert "exclusive=" in report
    assert "source=ExecutionTimingState" in report
