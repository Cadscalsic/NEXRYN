from __future__ import annotations

from runtime.experiments.route_value_shadow_replay import (
    HistoricalRouteValueMemory,
    NO_OBSERVABLE,
    POSITIVE,
    _exposure,
    _rank_routes,
)


def _manifest(task_id: str, route_id: str = "route.alpha", state: str = POSITIVE) -> dict:
    return {
        "task_id": task_id,
        "selected_routes": 1,
        "admitted_routes": 1,
        "route_cap": 1,
        "routes": [
            {
                "route_id": route_id,
                "route_family": "planner",
                "route_execution_id": f"{task_id}:{route_id}:execution",
                "route_position": 1,
                "contribution_state": state,
            }
        ],
    }


def test_historical_route_value_memory_is_idempotent() -> None:
    memory = HistoricalRouteValueMemory()
    manifest = _manifest("task-1")

    memory.index_manifest(manifest, "manifest-1")
    first_count = len(memory.observation_ids)
    memory.index_manifest(manifest, "manifest-1")

    assert first_count == 1
    assert len(memory.observation_ids) == first_count
    assert memory.duplicate_index_attempts == 1


def test_context_retrieval_uses_prior_matching_context_only() -> None:
    memory = HistoricalRouteValueMemory()
    route = _manifest("task-1")["routes"][0]

    before_index = memory.retrieve(route, _manifest("task-1"), mode="context")
    memory.index_manifest(_manifest("task-1"), "manifest-1")
    matching_context = memory.retrieve(route, _manifest("task-1"), mode="context")
    different_context = memory.retrieve(route, _manifest("task-2"), mode="context")

    assert before_index["context_match_level"] == "UNOBSERVED"
    assert matching_context["context_match_level"] == "EXACT_CONTEXT"
    assert matching_context["sample_count"] == 1
    assert different_context["context_match_level"] == "UNOBSERVED"


def test_unknown_route_retention_is_neutral_and_not_no_observable_penalty() -> None:
    routes = [
        {
            "route_id": "unknown.route",
            "route_family": "planner",
            "route_position": 1,
            "contribution_state": POSITIVE,
        },
        {
            "route_id": "known.no_observable",
            "route_family": "planner",
            "route_position": 2,
            "contribution_state": NO_OBSERVABLE,
        },
    ]
    retrievals = {
        "unknown.route": {
            "sample_count": 0,
            "shadow_value": 0.0,
            "unknown_route": True,
        },
        "known.no_observable": {
            "sample_count": 8,
            "shadow_value": 0.0,
            "unknown_route": False,
        },
    }

    ranked = _rank_routes(routes, retrievals, "UNCERTAINTY_AWARE_TIE_BREAK")
    exposure = _exposure(ranked, cap=1)

    assert ranked[0]["route_id"] == "unknown.route"
    assert exposure["useful"] == 1
    assert exposure["no_observable"] == 0
    assert exposure["unknown_retention_rate"] == 1.0
