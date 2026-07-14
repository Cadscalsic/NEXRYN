from runtime.timing import (
    CANONICAL_TIMING_SCOPES,
    ExecutionTimingUnificationEngine,
)


def _instance(runtime_id, execution_id, start, end, duration, parent=None, cpu=0.001):
    return {
        "runtime_id": runtime_id,
        "execution_id": execution_id,
        "execution_parent": parent,
        "execution_start": f"2026-07-14T10:00:{start:02d}+00:00",
        "execution_end": f"2026-07-14T10:00:{end:02d}+00:00",
        "duration_seconds": duration,
        "elapsed_seconds": duration,
        "cpu_time": cpu,
        "status": "COMPLETED",
    }


def test_canonical_timing_scope_definitions_are_explicit():
    required = {
        "BOOT_TIME",
        "TASK_SELECTION_TIME",
        "FIRST_TASK_START_LATENCY",
        "COGNITIVE_RUNTIME_TIME",
        "CHILD_RUNTIME_TIME",
        "POST_EXECUTION_COGNITIVE_TIME",
        "TRAINING_TIME",
        "REUSE_TIME",
        "GOVERNANCE_TIME",
        "FINALIZATION_TIME",
        "REPORT_GENERATION_TIME",
        "TOTAL_WALL_TIME",
    }

    assert required.issubset(CANONICAL_TIMING_SCOPES)
    assert all(CANONICAL_TIMING_SCOPES[scope]["owner"] for scope in required)
    assert all("included_components" in CANONICAL_TIMING_SCOPES[scope] for scope in required)
    assert all("excluded_components" in CANONICAL_TIMING_SCOPES[scope] for scope in required)


def test_sequential_child_execution_reconciles_parent_timing():
    report = ExecutionTimingUnificationEngine().build_report(
        execution_instances=[
            _instance("execution_runtime", "root", 0, 10, 10.0),
            _instance("reasoning_runtime", "reason", 1, 4, 3.0, "root"),
            _instance("truth_runtime", "truth", 4, 6, 2.0, "root"),
        ],
        total_wall_time=14.0,
        post_execution_cognitive_time=1.0,
        training_time=1.0,
        report_generation_time=2.0,
    )
    state = report["execution_timing_state"]
    parent = report["parent_timing"]

    assert state["cognitive_runtime_time"] == 10.0
    assert parent["parent_inclusive_duration"] == 10.0
    assert parent["child_duration_sum"] == 5.0
    assert parent["parent_exclusive_duration"] == 5.0
    assert state["accounted_wall_time"] == 14.0
    assert state["unattributed_time"] == 0.0
    assert state["timing_coverage"] == 1.0


def test_overlapping_child_execution_reports_overlap_without_parent_error():
    report = ExecutionTimingUnificationEngine().build_report(
        execution_instances=[
            _instance("execution_runtime", "root", 0, 10, 10.0),
            _instance("reasoning_runtime", "reason", 1, 7, 6.0, "root"),
            _instance("search_runtime", "search", 3, 8, 5.0, "root"),
        ],
        total_wall_time=10.0,
    )
    state = report["execution_timing_state"]

    assert state["parent_timing"]["child_duration_sum"] == 11.0
    assert state["overlap_time"] == 4.0
    assert state["double_counted_time"] == 4.0
    assert state["parent_timing"]["execution_relationship"] == "overlapping_or_parallel_execution"
    assert state["diagnostics"]["parent_child_boundary_violations"] == []


def test_post_training_and_report_timing_are_separate_scopes():
    report = ExecutionTimingUnificationEngine().build_report(
        execution_instances=[
            _instance("execution_runtime", "root", 0, 2, 2.0),
        ],
        total_wall_time=10.0,
        post_execution_cognitive_time=1.5,
        training_time=4.0,
        report_generation_time=2.5,
    )
    summary = report["timing_summary"]

    assert summary["cognitive_runtime_time"]["duration_seconds"] == 2.0
    assert summary["post_execution_cognitive_time"]["duration_seconds"] == 1.5
    assert summary["training_time"]["duration_seconds"] == 4.0
    assert summary["report_generation_time"]["duration_seconds"] == 2.5
    assert summary["total_wall_time"]["duration_seconds"] == 10.0


def test_unattributed_time_and_legacy_timing_semantics_are_visible():
    report = ExecutionTimingUnificationEngine().build_report(
        execution_instances=[
            _instance("execution_runtime", "root", 0, 2, 2.0),
        ],
        total_wall_time=8.0,
        legacy_report={"execution_time": 8.0, "duration": 2.0},
    )

    assert report["timing_summary"]["unattributed_time"]["duration_seconds"] == 6.0
    legacy = report["legacy_timing_semantics"]["deprecated_fields"]
    assert legacy["execution_time"]["deprecated"] is True
    assert legacy["execution_time"]["canonical_consumption_allowed"] is False


def test_timing_records_use_monotonic_measurement_contract():
    report = ExecutionTimingUnificationEngine().build_report(
        execution_instances=[
            _instance("execution_runtime", "root", 0, 2, 2.0),
            _instance("reuse_runtime", "reuse", 1, 2, 1.0, "root"),
        ],
        total_wall_time=2.0,
    )

    records = report["timing_records"]
    required_fields = {
        "timing_id",
        "execution_id",
        "runtime_id",
        "timing_name",
        "timing_scope",
        "timing_owner",
        "start_timestamp",
        "end_timestamp",
        "wall_duration_seconds",
        "cpu_duration_seconds",
        "inclusive_duration_seconds",
        "exclusive_duration_seconds",
        "included_components",
        "excluded_components",
        "parent_timing_id",
        "measurement_source",
        "measurement_method",
        "clock_type",
        "timing_version",
        "timing_status",
        "validation_status",
    }

    assert all(required_fields.issubset(record) for record in records)
    observed = [record for record in records if record["wall_duration_seconds"] > 0.0]
    assert all(record["clock_type"] == "monotonic_perf_counter" for record in observed)
    assert report["timing_summary"]["reuse_time"]["inclusion"] == (
        "included_inside_cognitive_runtime_time"
    )


def test_identical_timing_inputs_reproduce_same_summary():
    engine = ExecutionTimingUnificationEngine()
    kwargs = {
        "execution_instances": [
            _instance("execution_runtime", "root", 0, 4, 4.0),
            _instance("truth_runtime", "truth", 1, 3, 2.0, "root"),
        ],
        "total_wall_time": 7.0,
        "post_execution_cognitive_time": 1.0,
        "training_time": 2.0,
    }

    first = engine.build_report(**kwargs)
    second = engine.build_report(**kwargs)

    assert first["timing_summary"] == second["timing_summary"]
    assert first["parent_timing"] == second["parent_timing"]
