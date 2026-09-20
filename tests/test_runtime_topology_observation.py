from __future__ import annotations

from copy import deepcopy

from runtime.observability.runtime_topology_observation import (
    build_runtime_topology_observation_report,
    persist_runtime_topology_observation_report,
)


def _stage(name, status="completed", before=None, after=None):
    return {
        "stage_name": name,
        "status": status,
        "context_keys_before": before or [],
        "context_keys_after": after or [],
        "context_keys_added": [
            key for key in (after or []) if key not in set(before or [])
        ],
        "context_keys_removed": [
            key for key in (before or []) if key not in set(after or [])
        ],
        "context_keys_changed": [],
    }


def test_topology_observation_binds_to_current_run():
    report = build_runtime_topology_observation_report(
        runtime_context={
            "run_id": "run_current",
            "task_id": "task_a",
            "authoritative_execution_plan_reference": {
                "execution_plan_id": "plan_current",
            },
        },
        execution_trace=[_stage("task_loading")],
        pipeline_stages=[{"stage_name": "task_loading", "function_name": "task_loading_stage"}],
        execution_mode="adaptive",
        report_level="minimal",
        expected_run_id="run_current",
    )

    assert report["CURRENT_RUN_BINDING"] == "VALID"
    assert report["run_id"] == "run_current"
    assert report["execution_plan_id"] == "plan_current"
    assert report["task_id"] == "task_a"


def test_stage_order_matches_entered_trace_order():
    report = build_runtime_topology_observation_report(
        runtime_context={"run_id": "run_current"},
        execution_trace=[
            _stage("task_loading"),
            _stage("grid_analysis"),
            _stage("evaluation"),
        ],
        pipeline_stages=[
            {"stage_name": "task_loading", "function_name": "task_loading_stage"},
            {"stage_name": "grid_analysis", "function_name": "grid_analysis_stage"},
            {"stage_name": "evaluation", "function_name": "evaluation_stage"},
        ],
        expected_run_id="run_current",
    )

    assert [
        row["stage_name"] for row in report["stage_observations"]
    ] == ["task_loading", "grid_analysis", "evaluation"]
    assert [row["stage_index"] for row in report["stage_observations"]] == [1, 2, 3]


def test_stage_statuses_are_represented():
    report = build_runtime_topology_observation_report(
        runtime_context={"run_id": "run_current"},
        execution_trace=[
            _stage("task_loading", "completed"),
            _stage("self_improvement", "skipped"),
            _stage("evaluation", "failed"),
        ],
        pipeline_stages=[
            {"stage_name": "task_loading", "function_name": "task_loading_stage"},
            {"stage_name": "self_improvement", "function_name": "self_improvement_stage"},
            {"stage_name": "evaluation", "function_name": "evaluation_stage"},
        ],
        expected_run_id="run_current",
    )

    by_name = {row["stage_name"]: row for row in report["stage_observations"]}
    assert by_name["task_loading"]["completed"] is True
    assert by_name["self_improvement"]["skipped"] is True
    assert by_name["evaluation"]["failed"] is True


def test_context_delta_observation_does_not_mutate_runtime_context():
    context = {
        "run_id": "run_current",
        "input_grid": [[1]],
        "nested": {"value": [1, 2, 3]},
    }
    original = deepcopy(context)

    build_runtime_topology_observation_report(
        runtime_context=context,
        execution_trace=[_stage("task_loading", before=["run_id"], after=["run_id", "input_grid"])],
        pipeline_stages=[{"stage_name": "task_loading", "function_name": "task_loading_stage"}],
        expected_run_id="run_current",
    )

    assert context == original


def test_minimal_fast_success_path_can_be_represented(tmp_path):
    report = build_runtime_topology_observation_report(
        runtime_context={
            "run_id": "run_current",
            "pipeline_fast_minimal_return": {"enabled": True},
            "post_success_shutdown": {"enabled": True, "mode": "fast"},
            "episode_completed": True,
        },
        execution_trace=[_stage("evaluation", "completed")],
        pipeline_stages=[{"stage_name": "evaluation", "function_name": "evaluation_stage"}],
        execution_mode="adaptive",
        report_level="minimal",
        expected_run_id="run_current",
    )
    write_report = persist_runtime_topology_observation_report(
        report,
        artifact_directory=tmp_path,
    )

    assert report["fast_minimal_survival"] == "PROVEN"
    assert write_report["write_completed"] is True
    assert write_report["artifact_size_bytes"] > 0


def test_authority_is_observation_only():
    report = build_runtime_topology_observation_report(
        runtime_context={"run_id": "run_current"},
        execution_trace=[],
        pipeline_stages=[],
        expected_run_id="run_current",
    )

    assert report["authority"] == "OBSERVATION_ONLY"
    assert report["behavioral_authority"] == "NONE"
    assert report["not_consumable_as_authority"] == [
        "execution",
        "budget",
        "candidate",
        "repair",
        "evidence_acceptance",
        "truth",
        "identity",
        "learning",
        "task_selection",
    ]


def test_wrong_run_binding_is_invalid():
    report = build_runtime_topology_observation_report(
        runtime_context={"run_id": "run_current"},
        execution_trace=[],
        pipeline_stages=[],
        expected_run_id="run_other",
    )

    assert report["CURRENT_RUN_BINDING"] == "INVALID"
    assert report["current_run_binding_reason"] == "RUN_ID_MISMATCH"


def test_writer_failure_is_reported_without_raising(tmp_path):
    report = build_runtime_topology_observation_report(
        runtime_context={"run_id": "run_current"},
        execution_trace=[],
        pipeline_stages=[],
        expected_run_id="run_current",
    )
    blocked_path = tmp_path / "not_a_directory"
    blocked_path.write_text("occupied", encoding="utf-8")

    write_report = persist_runtime_topology_observation_report(
        report,
        artifact_directory=blocked_path,
    )

    assert write_report["write_completed"] is False
    assert write_report["observation_failure_preserves_task_execution"] is True


def test_topology_artifact_projection_is_bounded():
    report = build_runtime_topology_observation_report(
        runtime_context={
            "run_id": "run_current",
            "large_grid": [[index for index in range(30)] for _ in range(30)],
        },
        execution_trace=[
            _stage(
                "task_loading",
                before=["run_id"],
                after=["run_id", "large_grid"],
            )
        ],
        pipeline_stages=[{"stage_name": "task_loading", "function_name": "task_loading_stage"}],
        expected_run_id="run_current",
    )

    rendered = str(report)
    assert report["artifact_size_bytes"] < 25000
    assert "[0, 1, 2, 3" not in rendered


def test_pipeline_behavior_marker_is_observation_only():
    report = build_runtime_topology_observation_report(
        runtime_context={"run_id": "run_current", "episode_completed": True},
        execution_trace=[_stage("evaluation", "completed")],
        pipeline_stages=[{"stage_name": "evaluation", "function_name": "evaluation_stage"}],
        expected_run_id="run_current",
    )

    assert report["cognitive_behavior_change"] == "NONE"
    assert report["trace_source"] == "runtime.pipeline.legacy_pipeline.execution_trace"
