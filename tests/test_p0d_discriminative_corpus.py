import json

import pytest

from runtime.budget import (
    EXPERIMENTAL_BUDGET_SOURCE,
    P0D_INITIAL_SCREENING_CONFIGS,
    P0dCorpusContractError,
    classify_capacity_exposure,
    classify_search_dilution,
    cognitive_demand_profile,
    create_state_snapshot,
    freeze_discriminative_corpus,
    inventory_task_file,
    production_budget_snapshot,
    validate_budget_authority_measurement,
    validate_demand_profile,
    validate_state_fingerprint,
)


def _write_task(directory, name, metadata=None):
    path = directory / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "train": [
                    {
                        "input": [[0, 1, 0], [0, 0, 0], [2, 0, 0]],
                        "output": [[0, 3, 0], [0, 0, 0], [2, 0, 4]],
                    }
                ],
                "test": [{"input": [[0, 1, 0], [0, 0, 0], [2, 0, 0]]}],
                "nexryn_metadata": metadata or {},
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    return path


def _elite_metadata(task_id="elite_probe"):
    return {
        "task_id": task_id,
        "elite_cognitive_task": True,
        "elite_category": "elite_multi_domain",
        "domain_count": 5,
        "target_concepts": ["spatial_reasoning", "topological_reasoning"],
        "target_domains": ["Spatial", "Topology", "Color", "Identity", "Growth"],
        "multi_step_reasoning": True,
        "program_composition_required": True,
        "transformation_sequence_required": True,
        "operational_capability_composition_required": True,
        "novel_abstraction_required": True,
        "multiple_valid_solution_strategies": True,
        "deficiency_targets": ["validation_gaps", "low_operational_yield"],
        "required_operational_capabilities": ["program_generation"],
        "composite_capabilities": ["Pattern Completion", "Color Transformation"],
    }


def test_stable_task_fingerprint_is_path_independent(tmp_path):
    task_a = _write_task(tmp_path / "root_a", "same.json", _elite_metadata("same"))
    task_b = _write_task(tmp_path / "root_b", "same.json", _elite_metadata("same"))
    inv_a = [inventory_task_file(task_a, task_source="test")]
    inv_b = [inventory_task_file(task_b, task_source="test")]

    frozen_a = freeze_discriminative_corpus(inv_a, ["same"])
    frozen_b = freeze_discriminative_corpus(inv_b, ["same"])

    assert frozen_a.task_set_fingerprint == frozen_b.task_set_fingerprint
    assert "root_a" not in frozen_a.task_set_fingerprint
    assert "root_b" not in frozen_b.task_set_fingerprint


def test_demand_profile_schema_and_unknown_preservation():
    profile = cognitive_demand_profile(task_id="plain_task")

    validate_demand_profile(profile)
    assert profile["candidate_ambiguity"]["value"] == "UNKNOWN"
    assert profile["program_dependency"]["value"] == "UNKNOWN"
    assert profile["repair_pressure"]["value"] == "UNKNOWN"


def test_classification_provenance_is_required():
    profile = cognitive_demand_profile(task_id="plain_task")
    bad = dict(profile)
    bad["route_demand"] = dict(bad["route_demand"])
    bad["route_demand"]["evidence"] = ""

    with pytest.raises(P0dCorpusContractError):
        validate_demand_profile(bad)


def test_inventory_uses_content_and_metadata_not_file_name_only(tmp_path):
    task = _write_task(tmp_path, "misleading_rotation_name.json", _elite_metadata("elite_probe"))

    item = inventory_task_file(task, task_source="unit")

    assert item["task_id"] == "elite_probe"
    assert item["task_family"] == "elite_multi_domain"
    assert item["characteristics"]["rotation"]["value"] == "UNKNOWN"
    assert item["characteristics"]["multi_step_reasoning"]["value"] is True
    assert item["cognitive_demand_profile"]["depth_demand"]["value"] == "HIGH"


def test_corpus_freeze_preserves_order_and_rejects_late_mutation(tmp_path):
    first = _write_task(tmp_path, "a.json", _elite_metadata("a"))
    second = _write_task(tmp_path, "b.json", _elite_metadata("b"))
    inventory = [
        inventory_task_file(first, task_source="unit"),
        inventory_task_file(second, task_source="unit"),
    ]

    frozen = freeze_discriminative_corpus(inventory, ["b", "a"])

    assert [task["task_id"] for task in frozen.selected_tasks] == ["b", "a"]
    with pytest.raises(TypeError):
        frozen.selected_tasks[0]["task_id"] = "mutated"


def test_corpus_freeze_rejects_unknown_or_duplicate_task(tmp_path):
    task = _write_task(tmp_path, "a.json", _elite_metadata("a"))
    inventory = [inventory_task_file(task, task_source="unit")]

    with pytest.raises(P0dCorpusContractError):
        freeze_discriminative_corpus(inventory, ["a", "a"])
    with pytest.raises(P0dCorpusContractError):
        freeze_discriminative_corpus(inventory, ["missing"])


def test_state_fingerprint_validation_detects_changes(tmp_path):
    root = tmp_path / "repo"
    surface = root / "runtime" / "cache"
    surface.mkdir(parents=True)
    (surface / "state.json").write_text("{}", encoding="utf-8")
    observed = validate_state_fingerprint(
        repository_root=root,
        state_surfaces=["runtime/cache"],
        expected_state_fingerprint="not-the-fingerprint",
    )

    assert observed["valid"] is False
    assert observed["observed_state_fingerprint"].startswith("state_sha256_")


def test_state_snapshot_preserves_missing_surface_as_missing(tmp_path):
    root = tmp_path / "repo"
    (root / "runtime" / "cache").mkdir(parents=True)
    (root / "runtime" / "cache" / "state.json").write_text("{}", encoding="utf-8")

    snapshot = create_state_snapshot(
        repository_root=root,
        snapshot_root=tmp_path / "snapshot",
        state_surfaces=["runtime/cache", "memory"],
    )

    assert {
        (entry["path"], entry["kind"])
        for entry in snapshot["state_identity_entries"]
    } == {
        ("memory", "missing"),
        ("runtime/cache/state.json", "file"),
    }


def test_budget_authority_validation_accepts_matching_experimental_grant():
    measurement = {
        "authority_source": EXPERIMENTAL_BUDGET_SOURCE,
        "requested_max_active_routes": 3,
        "granted_max_active_routes": 3,
        "effective_max_active_routes": 3,
        "requested_max_reasoning_depth": 2,
        "granted_max_reasoning_depth": 2,
        "effective_max_reasoning_depth": 2,
        "realized_usage": {
            "admitted_routes": 3,
            "peak_active_routes": 2,
            "entered_reasoning_depth": 2,
            "completed_reasoning_depth": 2,
        },
    }

    assert validate_budget_authority_measurement(measurement) == []


def test_budget_authority_validation_rejects_mismatch_and_realized_overrun():
    measurement = {
        "authority_source": "COGNITIVE_BUDGET_REPORT",
        "requested_max_active_routes": 3,
        "granted_max_active_routes": 2,
        "effective_max_active_routes": 2,
        "requested_max_reasoning_depth": 2,
        "granted_max_reasoning_depth": 2,
        "effective_max_reasoning_depth": 2,
        "realized_usage": {
            "admitted_routes": 3,
            "peak_active_routes": 3,
            "entered_reasoning_depth": 2,
            "completed_reasoning_depth": 2,
        },
    }

    failures = validate_budget_authority_measurement(measurement)

    assert "AUTHORITY_SOURCE_NOT_EXPERIMENTAL_BUDGET_GRANT" in failures
    assert "REQUESTED_MAX_ACTIVE_ROUTES_GRANT_EFFECTIVE_MISMATCH" in failures
    assert "ADMITTED_ROUTES_EXCEEDS_EFFECTIVE_CEILING" in failures


def test_capacity_exposure_not_exposed_when_ceiling_increases_without_realized_use():
    result = classify_capacity_exposure(
        effective_budget_delta=2,
        realized_resource_delta=0,
        quality_delta=0,
    )

    assert result["capacity_exposure"] == "EXTRA_CAPACITY_UNUSED"
    assert result["mcv_quality"] == "NOT_EXPOSED"


def test_capacity_exposure_zero_only_when_realized_resource_increases():
    result = classify_capacity_exposure(
        effective_budget_delta=2,
        realized_resource_delta=1,
        quality_delta=0,
    )

    assert result["capacity_exposure"] == "EXTRA_CAPACITY_PARTIALLY_USED"
    assert result["mcv_quality"] == "ZERO_WITHIN_RESOLUTION"


def test_search_dilution_requires_negative_quality_or_search_signal():
    assert (
        classify_search_dilution(
            realized_resource_delta=2,
            final_quality_delta=0,
            search_efficiency_delta=0,
        )
        == "NO_DILUTION_EVIDENCE"
    )
    assert (
        classify_search_dilution(
            realized_resource_delta=2,
            final_quality_delta=-0.1,
            search_efficiency_delta=0,
            reproducible=True,
        )
        == "REPRODUCED_DILUTION_SIGNAL"
    )


def test_production_policy_non_mutation_and_initial_probe_configs():
    before = production_budget_snapshot()
    after = production_budget_snapshot()

    assert before == {"max_active_routes": 2, "max_reasoning_depth": 2}
    assert after == before
    assert P0D_INITIAL_SCREENING_CONFIGS == ("1/1", "2/2", "3/3", "4/4")
