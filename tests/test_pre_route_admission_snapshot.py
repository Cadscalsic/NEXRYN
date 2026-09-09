from __future__ import annotations

from copy import deepcopy

from runtime.budget.runtime_budget_enforcer import RuntimeBudgetEnforcer
from runtime.telemetry.pre_route_admission import (
    AUTHORITY,
    BEHAVIORAL_AUTHORITY,
    FORBIDDEN_FEATURE_FIELDS,
    SCHEMA_VERSION,
    TEMPORAL_INTEGRITY_VERIFIED,
    leakage_audit,
    snapshot_fingerprint,
)


def _budget(**overrides):
    budget = {
        "budget_snapshot_id": "budget_snapshot_a",
        "budget_source": "current_reasoning_budget",
        "run_id": "run_snapshot",
        "task_id": "task_snapshot",
        "max_active_routes": 2,
        "max_reasoning_depth": 2,
        "active_route_limit_scope": "TASK_CONCURRENT_ACTIVE_ROUTES",
        "reasoning_depth_limit_scope": "TASK_GOVERNED_REASONING_DEPTH",
    }
    budget.update(overrides)
    return budget


def _routes(count=4):
    return [
        {
            "route_id": f"route_{index}",
            "route_rank": index,
            "route_score": round(1.0 - index / 10, 3),
            "route_source": "governed_tool_route_selection",
            "route_family": "test_family",
        }
        for index in range(1, count + 1)
    ]


def _context(**overrides):
    routes = _routes()
    context = {
        "run_id": "run_snapshot",
        "task_id": "task_snapshot",
        "task_complexity_report": {
            "task_signature": "sig_snapshot",
            "object_count": 3,
            "transformation_count": 2,
            "spatial_complexity": 0.25,
            "process_complexity": 0.75,
            "temporal_complexity": 0.5,
            "estimated_cost": 0.8,
        },
        "grid_dimension_analysis": {
            "height": 5,
            "width": 6,
            "shape": [5, 6],
            "total_cells": 30,
        },
        "route_selection_report": {
            "available_routes": routes,
            "candidate_routes": routes,
            "active_routes": routes,
        },
    }
    context.update(overrides)
    return context


def _receipt(**overrides):
    routes = overrides.pop("routes", _routes())
    nodes = overrides.pop(
        "nodes",
        [{"materialization_state": "MATERIALIZED"} for _ in range(2)],
    )
    return RuntimeBudgetEnforcer().build_receipt(
        budget=overrides.pop("budget", _budget()),
        context=overrides.pop("context", _context()),
        execution_plan_id=overrides.pop("execution_plan_id", "plan_snapshot"),
        route_records=routes,
        nodes=nodes,
    )


def test_snapshot_created_before_admission_decision_and_temporal_state_verified():
    receipt = _receipt()

    assert receipt["pre_route_admission_snapshot_count"] == 4
    assert receipt["pre_route_admission_temporal_integrity_state"] == (
        TEMPORAL_INTEGRITY_VERIFIED
    )
    assert receipt["pre_route_admission_temporal_violation_count"] == 0
    assert all(
        link["snapshot_created_before_admission_decision"] is True
        for link in receipt["pre_route_admission_snapshot_linkages"]
    )


def test_snapshot_identity_is_unique_and_run_task_route_linkage_is_correct():
    receipt = _receipt()
    snapshots = receipt["pre_route_admission_snapshots"]

    assert len({row["snapshot_id"] for row in snapshots}) == 4
    assert all(row["run_id"] == "run_snapshot" for row in snapshots)
    assert all(row["task_id"] == "task_snapshot" for row in snapshots)
    assert [row["route_id"] for row in snapshots] == [
        "route_1",
        "route_2",
        "route_3",
        "route_4",
    ]
    assert [row["route_position"] for row in snapshots] == [1, 2, 3, 4]


def test_selected_admitted_and_executed_counts_are_temporal_pre_admission_state():
    receipt = _receipt()
    states = [row["route_context"] for row in receipt["pre_route_admission_snapshots"]]

    assert [row["selected_route_count"] for row in states] == [4, 4, 4, 4]
    assert [row["routes_already_admitted_count"] for row in states] == [0, 1, 2, 2]
    assert [row["routes_already_executed_count"] for row in states] == [0, 0, 0, 0]
    assert [row["remaining_route_capacity"] for row in states] == [2, 1, 0, 0]


def test_snapshot_payload_excludes_current_future_and_final_outcome_leakage():
    receipt = _receipt(
        context=_context(
            final_task_success=True,
            current_route_output_count=99,
            future_route_states=["future"],
            route_contribution_outcome="UNIQUE_USEFUL_CONTRIBUTION",
        )
    )

    for snapshot in receipt["pre_route_admission_snapshots"]:
        audit = leakage_audit(snapshot)
        assert audit["leakage_count"] == 0
        assert not (FORBIDDEN_FEATURE_FIELDS & set(snapshot.keys()))


def test_prior_route_state_is_limited_to_causally_available_counts():
    receipt = _receipt(
        context=_context(
            route_output_lineage_records=[
                {
                    "origin_route_id": "route_1",
                    "candidate_id": "candidate_1",
                    "producer_component": "producer_a",
                },
                {
                    "origin_route_id": "route_3",
                    "candidate_id": "candidate_future",
                    "producer_component": "producer_future",
                },
            ]
        )
    )
    snapshots = receipt["pre_route_admission_snapshots"]

    assert snapshots[0]["state_so_far"]["candidate_count_so_far"] == (
        "NOT_OBSERVED_PRE_ADMISSION"
    )
    assert snapshots[1]["state_so_far"]["candidate_count_so_far"] == 1
    assert snapshots[1]["state_so_far"]["candidate_source_count_so_far"] == 1
    assert snapshots[2]["state_so_far"]["candidate_count_so_far"] == 1


def test_snapshot_immutable_and_fingerprint_stable_after_route_execution_linkage():
    receipt = _receipt()
    snapshot = receipt["pre_route_admission_snapshots"][0]
    before = deepcopy(snapshot)
    link = receipt["pre_route_admission_snapshot_linkages"][0]

    assert snapshot_fingerprint(snapshot) == snapshot["snapshot_fingerprint"]
    assert link["snapshot_fingerprint_before"] == link[
        "snapshot_fingerprint_after_route_execution"
    ]
    assert snapshot == before
    assert receipt["pre_route_admission_snapshot_mutation_count"] == 0


def test_admission_and_contribution_outcomes_are_stored_separately():
    receipt = _receipt()
    snapshot = receipt["pre_route_admission_snapshots"][0]
    disposition = receipt["route_dispositions"][0]
    link = receipt["pre_route_admission_snapshot_linkages"][0]

    assert "admission_state" not in snapshot
    assert "contribution_state" not in snapshot
    assert disposition["pre_admission_snapshot_id"] == snapshot["snapshot_id"]
    assert disposition["admission_state"] == "ADMITTED"
    assert disposition["feature_state"] == "DECISION_OUTCOME"
    assert link["contribution_outcome_state"] == "PENDING_ROUTE_CONTRIBUTION_OUTCOME"


def test_snapshot_authority_is_observation_only_and_behavioral_authority_none():
    receipt = _receipt()

    assert receipt["pre_route_admission_snapshot_authority"] == AUTHORITY
    assert receipt["pre_route_admission_snapshot_behavioral_authority"] == (
        BEHAVIORAL_AUTHORITY
    )
    assert all(row["authority"] == AUTHORITY for row in receipt["pre_route_admission_snapshots"])
    assert all(
        row["behavioral_authority"] == BEHAVIORAL_AUTHORITY
        for row in receipt["pre_route_admission_snapshots"]
    )
    assert all(
        row["telemetry_consumed_by_cognition"] is False
        for row in receipt["pre_route_admission_snapshots"]
    )


def test_budget_authority_and_admission_behavior_are_unchanged():
    routes = _routes()
    before_routes = deepcopy(routes)
    receipt = _receipt(routes=routes)

    assert RuntimeBudgetEnforcer.system_name == "runtime_budget_enforcer"
    assert receipt["runtime_budget_state"] == "RUNTIME_BUDGET_FINALIZED"
    assert receipt["route_budget_enforcement_state"] == "ROUTE_BUDGET_LIMIT_REACHED"
    assert receipt["admitted_route_count"] == 2
    assert receipt["deferred_by_budget_route_count"] == 2
    assert routes == before_routes


def test_route_ordering_and_classification_are_unchanged_by_snapshots():
    receipt = _receipt()

    assert [row["route_id"] for row in receipt["route_dispositions"]] == [
        "route_1",
        "route_2",
        "route_3",
        "route_4",
    ]
    assert [row["budget_disposition"] for row in receipt["route_dispositions"]] == [
        "ROUTE_BUDGET_ADMITTED",
        "ROUTE_BUDGET_ADMITTED",
        "DEFERRED_BY_BUDGET",
        "DEFERRED_BY_BUDGET",
    ]


def test_snapshot_schema_and_overhead_are_reported_without_zero_claim():
    receipt = _receipt()
    overhead = receipt["pre_route_admission_overhead"]

    assert receipt["pre_route_admission_snapshot_schema_version"] == SCHEMA_VERSION
    assert overhead["snapshot_bytes"] > 0
    assert overhead["total_snapshot_bytes_per_task"] > 0
    assert "snapshot_serialization_time" in overhead
    assert "total_snapshot_time_per_task" in overhead


def test_cognitive_consumers_remain_zero():
    receipt = _receipt()

    assert receipt["pre_route_admission_consumed_by_cognition"] is False
    assert all(
        row.get("telemetry_consumed_by_cognition") is False
        for row in receipt["pre_route_admission_snapshots"]
    )
