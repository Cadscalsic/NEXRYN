from runtime.reporting.report_timing_semantics import ReportTimingSemanticEngine


def _record(scope, duration, source="ExecutionTimingState", start=None, end=None):
    data = {
        "timing_id": f"report:{scope}:{source}",
        "execution_id": "exec-1",
        "report_id": "report-1",
        "timing_scope": scope,
        "inclusive_duration_seconds": duration,
        "exclusive_duration_seconds": duration,
        "measurement_source": source,
        "measurement_method": "unit_test",
        "clock_type": "monotonic_perf_counter",
        "timing_status": "OBSERVED",
        "validation_status": "VALID",
    }
    if start is not None:
        data["start_timestamp"] = f"2026-07-14T10:00:{start:02d}+00:00"
    if end is not None:
        data["end_timestamp"] = f"2026-07-14T10:00:{end:02d}+00:00"
    return data


def test_complete_report_lifecycle_timing_reconciles_phase_union():
    report = ReportTimingSemanticEngine().reconcile(
        timing_records=[
            _record("REPORT_INPUT_COLLECTION_TIME", 1.0, start=0, end=1),
            _record("REPORT_BINDING_TIME", 2.0, start=1, end=3),
            _record("REPORT_COMPRESSION_TIME", 1.0, start=3, end=4),
            _record("FINAL_REPORT_RENDERING_TIME", 0.5, start=4, end=5),
        ],
        runtime_metadata={"execution_id": "exec-1"},
    )

    summary = report["report_timing_summary"]
    assert summary["report_lifecycle_total_time"] == 5.0
    assert summary["report_phase_duration_sum"] == 4.5
    assert summary["report_phase_interval_union"] == 5.0
    assert summary["final_report_rendering_time"] == 0.5
    assert report["report_timing_semantics_valid"] is True


def test_overlapping_report_phases_reconcile_without_raw_sum_total():
    report = ReportTimingSemanticEngine().reconcile(
        timing_records=[
            _record("REPORT_BINDING_TIME", 4.0, start=0, end=4),
            _record("REPORT_COMPRESSION_TIME", 3.0, start=2, end=5),
        ],
    )

    summary = report["report_timing_summary"]
    assert summary["report_phase_duration_sum"] == 7.0
    assert summary["report_phase_interval_union"] == 5.0
    assert summary["report_overlap_duration"] == 2.0
    assert summary["report_lifecycle_total_time"] == 5.0


def test_final_rendering_and_compression_sources_stay_isolated():
    report = ReportTimingSemanticEngine().reconcile(
        timing_records=[
            _record("REPORT_GENERATION_TIME", 0.0341),
            _record("REPORT_COMPRESSION_TIME", 0.14),
        ],
    )
    summary = report["report_timing_summary"]

    assert summary["final_report_rendering_time"] == 0.0341
    assert summary["report_compression_time"] == 0.14
    assert summary["report_lifecycle_total_time"] != summary["final_report_rendering_time"]


def test_legacy_ambiguous_report_generation_field_is_diagnostic_only():
    report = ReportTimingSemanticEngine().reconcile(
        timing_state={"report_generation_time": 1.0185},
        performance={"runtime_breakdown": {"report_time": 1.0185}},
    )

    ambiguous = report["report_timing_summary"]["ambiguous_legacy_timing_fields"]
    assert {item["legacy_field"] for item in ambiguous} == {
        "report_generation_time",
        "report_time",
    }
    assert all(item["normal_reporting_allowed"] is False for item in ambiguous)


def test_canonical_source_selection_and_conflict_detection():
    report = ReportTimingSemanticEngine().reconcile(
        timing_records=[
            _record("REPORT_BINDING_TIME", 0.1, source="Final Report Renderer"),
            _record("REPORT_BINDING_TIME", 0.2, source="Runtime Metric Attribution"),
        ],
    )

    binding = next(
        node for node in report["report_timing_nodes"]
        if node["timing_scope"] == "REPORT_BINDING_TIME"
    )
    assert binding["canonical_timing_source"] == "Final Report Renderer"
    assert binding["source_conflict_detected"] is True
    assert report["report_timing_semantics_valid"] is False


def test_conditional_absent_phases_are_not_fabricated_as_zero():
    report = ReportTimingSemanticEngine().reconcile(
        timing_records=[_record("FINAL_REPORT_RENDERING_TIME", 0.0341)],
    )

    scopes = {node["timing_scope"] for node in report["report_timing_nodes"]}
    assert "TECHNICAL_APPENDIX_SERIALIZATION_TIME" not in scopes
    assert report["report_timing_summary"]["technical_appendix_serialization_time"] is None
