from __future__ import annotations

from collections import Counter

from runtime.experiments.route_value_context_granularity import (
    CURRENT_CONTEXT_FIELDS,
    _aggregate_replay,
    _geometry_from_counts,
    bucket_key,
)


def test_bucket_geometry_reports_single_use_fragmentation() -> None:
    geometry = _geometry_from_counts(Counter({"a": 1, "b": 1, "c": 2}))

    assert geometry["observation_count"] == 4
    assert geometry["bucket_count"] == 3
    assert geometry["single_observation_bucket_count"] == 2
    assert geometry["single_observation_bucket_rate"] == 0.666667
    assert geometry["multi_observation_bucket_count"] == 1


def test_task_signature_is_part_of_current_exact_context() -> None:
    route = {
        "route_id": "route.alpha",
        "route_family": "planner",
        "route_position": 1,
    }
    first_manifest = {"task_id": "task-a", "selected_routes": 1, "route_cap": 1}
    second_manifest = {"task_id": "task-b", "selected_routes": 1, "route_cap": 1}

    first_key = bucket_key(route, first_manifest, tuple(CURRENT_CONTEXT_FIELDS))
    second_key = bucket_key(route, second_manifest, tuple(CURRENT_CONTEXT_FIELDS))
    without_task = tuple(field for field in CURRENT_CONTEXT_FIELDS if field != "task_signature")

    assert first_key != second_key
    assert bucket_key(route, first_manifest, without_task) == bucket_key(route, second_manifest, without_task)


def test_replay_false_transfer_rate_is_normalized_by_admitted_routes() -> None:
    rows = [
        {
            "level": "L1",
            "strategy": "S",
            "admitted_count": 4,
            "false_transfer_count": 2,
            "useful_delta": 0,
            "no_observable_delta": 0,
            "low_value_delta": 0,
            "unknown_retention_rate": 0.5,
            "useful_route_suppression_count": 0,
            "exploration_loss_count": 0,
        },
        {
            "level": "L1",
            "strategy": "S",
            "admitted_count": 2,
            "false_transfer_count": 1,
            "useful_delta": 0,
            "no_observable_delta": 0,
            "low_value_delta": 0,
            "unknown_retention_rate": 0.0,
            "useful_route_suppression_count": 0,
            "exploration_loss_count": 0,
        },
    ]

    aggregate = _aggregate_replay(rows)

    assert aggregate[0]["false_transfer_rate"] == 0.5
