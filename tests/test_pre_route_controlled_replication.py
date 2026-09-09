from __future__ import annotations

import json
from pathlib import Path

from runtime.experiments.pre_route_controlled_replication import (
    run_pre_route_controlled_replication,
)


def _snapshot(run_id, task_id, route_id, position):
    return {
        "schema_version": "pre_route_admission_snapshot.v1",
        "authority": "OBSERVATION_ONLY",
        "behavioral_authority": "NONE",
        "snapshot_id": f"snapshot_{task_id}_{route_id}",
        "snapshot_fingerprint": f"fingerprint_{task_id}_{route_id}",
        "run_id": run_id,
        "task_id": task_id,
        "route_id": route_id,
        "route_position": position,
        "capture_stage": "runtime_budget_enforcer.pre_route_admission",
        "temporal_integrity_state": "PRE_ADMISSION_TEMPORAL_INTEGRITY_VERIFIED",
        "leakage_fields": [],
        "task_features": {
            "task_signature": f"sig_{task_id}",
            "object_count": 8 if task_id == "task_positive.json" else 2,
            "transformation_count": 2,
            "estimated_cognitive_cost": 0.9,
        },
        "route_context": {
            "route_family": "governed_evaluation_route_admission",
            "selected_route_count": 6,
            "current_route_budget": 6,
            "remaining_route_capacity": 7 - position,
            "routes_already_admitted_count": position - 1,
            "routes_already_executed_count": 0,
        },
        "state_so_far": {
            "candidate_count_so_far": "NOT_OBSERVED_PRE_ADMISSION",
            "route_useful_count_so_far": 0,
            "route_no_observable_count_so_far": 0,
        },
    }


def _route(task_id, route_id, position, state, executed=True):
    return {
        "route_execution_id": f"rex_{task_id}_{route_id}",
        "route_position": position,
        "route_id": route_id,
        "route_family": "governed_evaluation_route_admission",
        "admitted": executed,
        "executed": executed,
        "completed": executed,
        "output_count": 1 if state == "UNIQUE_USEFUL_CONTRIBUTION" else 0,
        "contribution_state": state,
    }


def _manifest(run_id, task_id, routes):
    return {
        "artifact_path": f"route_manifest_{task_id}.json",
        "run_id": run_id,
        "task_id": task_id,
        "route_cap": 6,
        "routes": routes,
    }


def _source_artifact(tmp_path: Path, *, duplicate_repeat=False):
    run_id = "run_replication"
    route_ids = [
        "contradiction_checks",
        "dependency_reasoning",
        "identity_governance",
        "object_tracking",
    ]
    tasks = ["task_negative.json", "task_positive.json"]
    snapshot_root = tmp_path / "snapshots"
    for task in tasks:
        task_dir = snapshot_root / run_id / f"task_{task}"
        task_dir.mkdir(parents=True, exist_ok=True)
        for offset, route_id in enumerate(route_ids, start=3):
            (task_dir / f"{offset}_{route_id}.json").write_text(
                json.dumps(_snapshot(run_id, task, route_id, offset)),
                encoding="utf-8",
            )
    positive_state = "UNIQUE_USEFUL_CONTRIBUTION"
    negative_state = "NO_OBSERVABLE_CONTRIBUTION"
    manifests = []
    for task in tasks:
        routes = []
        for position, route_id in enumerate(route_ids, start=3):
            state = (
                positive_state
                if task == "task_positive.json" and route_id == "identity_governance"
                else negative_state
            )
            routes.append(_route(task, route_id, position, state))
        routes.append(_route(task, "unmeasurable_route", 6, "CONTRIBUTION_NOT_MEASURABLE"))
        manifests.append(_manifest(run_id, task, routes))
    raw = [
        {
            "configuration_id": "route_cap_2",
            "route_cap": 2,
            "repeat_id": "repeat_001",
            "selected_task_files": tasks,
            "route_manifests": [],
        },
        {
            "configuration_id": "route_cap_6",
            "route_cap": 6,
            "repeat_id": "repeat_001",
            "selected_task_files": tasks,
            "route_manifests": manifests,
        },
    ]
    if duplicate_repeat:
        duplicate = dict(raw[1])
        duplicate["repeat_id"] = "repeat_002"
        raw.append(duplicate)
    report = {
        "investigation_id": "source_investigation",
        "raw_measurements": raw,
        "derived": {
            "comparability": {
                "task_order": tasks,
                "seed": 424242,
                "mode": "adaptive",
                "reasoning_depth": "2",
            },
            "aggregate_comparison": {
                "paired_improved_with_6": 0,
                "paired_regressed_with_6": 0,
                "paired_unchanged": 2,
                "delta_exact_success_rate": 0,
                "delta_mean_accuracy": 0,
                "delta_mean_final_score": 0,
            },
        },
    }
    source = tmp_path / "active_route_budget_effectiveness.json"
    source.write_text(json.dumps(report), encoding="utf-8")
    return source, snapshot_root


def test_canonical_dataset_links_snapshots_and_uses_only_executed_marginal_routes(tmp_path):
    source, snapshot_root = _source_artifact(tmp_path)

    summary = run_pre_route_controlled_replication(
        source,
        output_root=tmp_path / "out",
        snapshot_root=snapshot_root,
        timestamp="20260908_test",
    )
    dataset = json.loads(
        (tmp_path / "out" / "20260908_test" / "pre_route_canonical_dataset.json").read_text()
    )

    assert summary["raw_marginal_route_rows"] == 8
    assert dataset["excluded_contribution_not_measurable"] == 2
    assert dataset["snapshot_linkage_failures"] == 0
    assert all(row["snapshot_id"] for row in dataset["rows"])
    assert {row["route_position"] for row in dataset["rows"]} == {3, 4, 5, 6}


def test_outcome_fields_are_excluded_and_not_observed_is_preserved(tmp_path):
    source, snapshot_root = _source_artifact(tmp_path)

    run_pre_route_controlled_replication(
        source,
        output_root=tmp_path / "out",
        snapshot_root=snapshot_root,
        timestamp="20260908_test",
    )
    dataset = json.loads(
        (tmp_path / "out" / "20260908_test" / "pre_route_canonical_dataset.json").read_text()
    )

    for row in dataset["rows"]:
        assert all("target_" not in name for name in row["features"])
        assert all("contribution_state" not in name for name in row["features"])
    assert any(
        value == "NOT_OBSERVED_PRE_ADMISSION"
        for row in dataset["rows"]
        for value in row["features"].values()
    )


def test_deterministic_replay_reduces_effective_independent_n(tmp_path):
    source, snapshot_root = _source_artifact(tmp_path, duplicate_repeat=True)

    summary = run_pre_route_controlled_replication(
        source,
        output_root=tmp_path / "out",
        snapshot_root=snapshot_root,
        timestamp="20260908_test",
    )

    assert summary["deterministic_replay_detected"] is True
    assert summary["raw_marginal_route_rows"] > summary[
        "effective_independent_observation_count"
    ]


def test_route_position_confounding_and_disabled_permutation_are_reported(tmp_path):
    source, snapshot_root = _source_artifact(tmp_path)

    summary = run_pre_route_controlled_replication(
        source,
        output_root=tmp_path / "out",
        snapshot_root=snapshot_root,
        timestamp="20260908_test",
    )
    confounding = json.loads(
        (tmp_path / "out" / "20260908_test" / "pre_route_route_position_confounding.json").read_text()
    )
    feasibility = json.loads(
        (tmp_path / "out" / "20260908_test" / "pre_route_permutation_feasibility.json").read_text()
    )

    assert confounding["classification"] == "FULLY_CONFOUNDED"
    assert summary["position_permutation_used"] == "NO"
    assert feasibility["permutation_used_this_run"] == "NO"
    assert feasibility["production_route_order_changed"] == "NO"


def test_p2_gate_rejects_sparse_fully_confounded_single_context_evidence(tmp_path):
    source, snapshot_root = _source_artifact(tmp_path)

    summary = run_pre_route_controlled_replication(
        source,
        output_root=tmp_path / "out",
        snapshot_root=snapshot_root,
        timestamp="20260908_test",
    )

    assert summary["p2_gate_passed"] is False
    assert summary["current_evidence_level"] == "P1_CANDIDATE_SIGNAL_OBSERVED"
    assert summary["adaptive_policy_patch_allowed"] is False


def test_internal_value_remains_separate_from_decisive_final_value(tmp_path):
    source, snapshot_root = _source_artifact(tmp_path)

    summary = run_pre_route_controlled_replication(
        source,
        output_root=tmp_path / "out",
        snapshot_root=snapshot_root,
        timestamp="20260908_test",
    )
    trace = json.loads(
        (tmp_path / "out" / "20260908_test" / "pre_route_internal_value_trace.json").read_text()
    )
    final = json.loads(
        (tmp_path / "out" / "20260908_test" / "pre_route_final_outcome_analysis.json").read_text()
    )

    assert trace["highest_supported_level"] == "L3_INTERNAL_USEFUL_CONTRIBUTION"
    assert final["decisive_final_value"] == "NO"
    assert summary["p3_claim_allowed"] is False


def test_authority_and_cognitive_consumers_remain_zero(tmp_path):
    source, snapshot_root = _source_artifact(tmp_path)

    summary = run_pre_route_controlled_replication(
        source,
        output_root=tmp_path / "out",
        snapshot_root=snapshot_root,
        timestamp="20260908_test",
    )

    assert summary["experiment_harness_authority"] == "NONE"
    assert summary["telemetry_authority"] == "OBSERVATION_ONLY"
    assert summary["cognitive_consumer_count"] == 0
    assert summary["production_route_order_changed"] == "NO"
    assert summary["production_route_budget_changed"] == "NO"
    assert summary["route_classifier_changed"] == "NO"
