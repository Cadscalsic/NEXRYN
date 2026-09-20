from runtime.timing import HierarchicalTimingReconciliationEngine


def _record(timing_id, scope, start, end, parent=None, source="ExecutionTimingState"):
    return {
        "timing_id": timing_id,
        "execution_id": "exec-1",
        "timing_name": scope.lower(),
        "timing_scope": scope,
        "parent_timing_id": parent,
        "start_timestamp": f"2026-07-14T10:00:{start:02d}+00:00",
        "end_timestamp": f"2026-07-14T10:00:{end:02d}+00:00",
        "inclusive_duration_seconds": float(end - start),
        "exclusive_duration_seconds": float(end - start),
        "measurement_source": source,
        "validation_status": "VALID",
    }


def test_sequential_child_intervals_compute_parent_exclusive_time():
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("task", "TASK_EXECUTION_TIME", 0, 10),
        _record("context", "CONTEXT_TIME", 1, 4, "task"),
        _record("reasoning", "REASONING_TIME", 4, 7, "task"),
    ], total_wall_time=10.0)

    task = next(row for row in report["timing_hierarchy_summary"] if row["timing_id"] == "task")
    assert task["child_duration_sum"] == 6.0
    assert task["child_interval_union_duration"] == 6.0
    assert task["exclusive_duration"] == 4.0


def test_overlapping_and_parallel_children_use_interval_union_not_sum():
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("task", "TASK_EXECUTION_TIME", 0, 10),
        _record("reasoning", "REASONING_TIME", 1, 7, "task"),
        _record("search", "SEARCH_TIME", 3, 8, "task"),
    ], total_wall_time=10.0)

    task = next(row for row in report["timing_hierarchy_summary"] if row["timing_id"] == "task")
    assert task["child_duration_sum"] == 11.0
    assert task["child_interval_union_duration"] == 7.0
    assert task["parallel_overlap_duration"] == 4.0
    assert task["exclusive_duration"] == 3.0
    assert report["overlap_detected"] is True


def test_duplicate_source_reconciliation_selects_one_canonical_record():
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("reason-a", "REASONING_TIME", 0, 5, source="ExecutionTimingState"),
        _record("reason-b", "REASONING_TIME", 0, 5, source="Runtime Metric Attribution"),
    ], total_wall_time=5.0)

    reasoning = [
        row for row in report["timing_hierarchy_summary"]
        if row["stage_name"] == "Reasoning"
    ]
    assert len(reasoning) == 1
    assert reasoning[0]["canonical_timing_source"] == "ExecutionTimingState"
    assert reasoning[0]["alternate_timing_sources"] == ["Runtime Metric Attribution"]


def test_cycle_rejection_and_boundary_violation_detection():
    cycle_a = _record("a", "CONTEXT_TIME", 1, 2, "b")
    cycle_b = _record("b", "REASONING_TIME", 2, 3, "a")
    outside = _record("outside", "SEARCH_TIME", 8, 12, "task")
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("task", "TASK_EXECUTION_TIME", 0, 10),
        cycle_a,
        cycle_b,
        outside,
    ], total_wall_time=10.0)

    violations = {item["violation"] for item in report["timing_boundary_violations"]}
    assert "invalid_parent_child_cycle" in violations
    assert "child_interval_outside_parent_boundary" in violations
    assert report["timing_hierarchy_valid"] is False


def test_resource_percentages_sum_to_at_most_one_hundred_and_are_stable():
    engine = HierarchicalTimingReconciliationEngine()
    records = [
        _record("task", "TASK_EXECUTION_TIME", 0, 10),
        _record("context", "CONTEXT_TIME", 0, 4, "task"),
        _record("reasoning", "REASONING_TIME", 4, 10, "task"),
    ]

    first = engine.reconcile(records, total_wall_time=10.0)
    second = engine.reconcile(records, total_wall_time=10.0)

    assert first["resource_percentage_sum"] <= 100.0001
    assert first["timing_hierarchy_summary"] == second["timing_hierarchy_summary"]
    assert first["resource_consumption_ranking"] == second["resource_consumption_ranking"]


def test_per_task_execution_records_are_children_not_additive_peers():
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("task-parent", "TASK_EXECUTION_TIME", 0, 50),
        _record("task-a", "Task Execution:Arc Concept Occlusion Masking", 0, 12),
        _record("task-b", "Task Execution:Arc Generated Topology Change", 12, 25),
        _record("task-c", "Task Execution:Arc Generated Scaling Density", 25, 50),
    ], total_wall_time=55.0, active_compute_time=109.0)

    parent = next(row for row in report["timing_hierarchy_summary"] if row["timing_id"] == "task-parent")
    child_rows = [
        row for row in report["timing_hierarchy_summary"]
        if str(row["stage_name"]).startswith("Task Execution:Arc")
    ]
    ranking_names = [row["stage_name"] for row in report["resource_consumption_ranking"]]

    assert parent["exclusive_duration"] == 0.0
    assert parent["child_interval_union_duration"] == 50.0
    assert {row["relationship_type"] for row in child_rows} == {"CHILD"}
    assert "Task Execution" not in ranking_names
    assert report["active_compute_time"] == 50.0
    assert report["active_compute_time"] <= report["timing_hierarchy_summary"][0]["inclusive_duration"]


def test_duplicate_context_and_assemble_final_context_are_not_ranked_twice():
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("task-parent", "TASK_EXECUTION_TIME", 0, 10),
        _record("context", "CONTEXT_TIME", 1, 3, "task-parent"),
        _record("assemble-final-context", "ASSEMBLE_FINAL_CONTEXT", 1, 3),
    ], total_wall_time=10.0)

    context_like = [
        row for row in report["resource_consumption_ranking"]
        if row["stage_name"] in {"Context", "Assemble Final Context"}
    ]

    assert len(context_like) == 1
    assert report["active_compute_time"] == 10.0


def test_reasoning_overlap_with_per_task_execution_is_not_double_counted():
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("task-parent", "TASK_EXECUTION_TIME", 0, 40),
        _record("reasoning", "REASONING_TIME", 0, 30),
        _record("task-a", "Task Execution:Arc A", 5, 15),
        _record("task-b", "Task Execution:Arc B", 15, 30),
    ], total_wall_time=40.0, active_compute_time=65.0)

    reasoning = next(
        row for row in report["timing_hierarchy_summary"]
        if row["timing_id"] == "reasoning"
    )
    ranking = {
        row["timing_id"]: row
        for row in report["resource_consumption_ranking"]
    }

    assert reasoning["relationship_type"] == "OVERLAPPING"
    assert reasoning["reasoning_task_overlap_duration"] == 25.0
    assert reasoning["resource_exclusive_duration"] == 5.0
    assert ranking["reasoning"]["exclusive_duration"] == 5.0
    assert report["active_compute_time"] == 40.0
    assert report["resource_percentage_sum"] == 100.0


def test_reasoning_before_tasks_remains_independent_resource_consumer():
    report = HierarchicalTimingReconciliationEngine().reconcile([
        _record("task-parent", "TASK_EXECUTION_TIME", 0, 40),
        _record("reasoning", "REASONING_TIME", 0, 10),
        _record("task-a", "Task Execution:Arc A", 10, 20),
        _record("task-b", "Task Execution:Arc B", 20, 40),
    ], total_wall_time=40.0)

    ranking = {
        row["timing_id"]: row
        for row in report["resource_consumption_ranking"]
    }

    assert ranking["reasoning"]["exclusive_duration"] == 10.0
    assert report["active_compute_time"] == 40.0
