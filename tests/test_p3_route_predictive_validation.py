from runtime.experiments.p3_route_predictive_validation import (
    default_held_out_task_ids,
    development_task_ids,
    freeze_signal_contract,
    run_p3_analysis,
    score_snapshot,
)


def _snapshot(task_id="task_001.json", route_id="identity_governance", position=3):
    return {
        "snapshot_id": f"snap_{task_id}_{route_id}_{position}",
        "run_id": "run_test",
        "task_id": task_id,
        "route_id": route_id,
        "route_position": position,
        "admission_sequence_index": position,
        "task_features": {
            "object_count": 2,
            "transformation_count": 1,
            "grid_cell_count": 25,
        },
        "route_context": {
            "route_family": "governed_evaluation_route_admission",
            "remaining_route_capacity": 3,
            "routes_already_admitted_count": position - 1,
        },
        "state_so_far": {
            "prior_useful_route_count": 0,
            "prior_no_observable_route_count": 1,
        },
    }


def _raw_run(state="UNIQUE_USEFUL_CONTRIBUTION"):
    return {
        "returncode": 0,
        "timed_out": False,
        "human_report": {"Run Id": "run_test"},
        "route_manifests": [
            {
                "run_id": "run_test",
                "task_id": "task_001.json",
                "routes": [
                    {
                        "route_id": "identity_governance",
                        "route_position": 3,
                        "executed": True,
                        "contribution_state": state,
                    }
                ],
            }
        ],
    }


def test_task03_excluded_from_default_held_out():
    assert "elite_cognitive_task_03.json" in development_task_ids()
    assert "elite_cognitive_task_03.json" not in default_held_out_task_ids()


def test_held_out_contamination_detector(tmp_path):
    dev = development_task_ids()
    held = ["elite_cognitive_task_03.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    prediction = score_snapshot(_snapshot("elite_cognitive_task_03.json"), contract)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[prediction],
        output_dir=tmp_path,
    )
    assert result["held_out_contamination_count"] == 1
    assert result["p3_gate_passed"] is False


def test_frozen_signal_fingerprint_stable():
    dev = development_task_ids()
    held = default_held_out_task_ids()
    first = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    second = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    assert first["signal_contract_fingerprint"] == second["signal_contract_fingerprint"]


def test_prediction_before_outcome_and_behavioral_none(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    prediction = score_snapshot(_snapshot(), contract)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[prediction],
        output_dir=tmp_path,
    )
    assert result["temporal_integrity_failures"] == 0
    assert result["behavioral_authority"] == "NONE"


def test_zero_positive_classified_not_estimable(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    prediction = score_snapshot(_snapshot(), contract)
    result = run_p3_analysis(
        raw_run=_raw_run("NO_OBSERVABLE_CONTRIBUTION"),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[prediction],
        output_dir=tmp_path,
    )
    assert result["current_evidence_level"] == "P3_NOT_ESTIMABLE_POSITIVE_SCARCITY"
    assert result["failure_mode"] == "NO_HELD_OUT_POSITIVES"


def test_contribution_not_measurable_excluded(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    prediction = score_snapshot(_snapshot(), contract)
    result = run_p3_analysis(
        raw_run=_raw_run("CONTRIBUTION_NOT_MEASURABLE"),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[prediction],
        output_dir=tmp_path,
    )
    assert result["measurable_evaluation_rows"] == 0


def test_required_artifacts_written(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    prediction = score_snapshot(_snapshot(), contract)
    run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[prediction],
        output_dir=tmp_path,
    )
    assert (tmp_path / "p3_signal_contract.json").exists()
    assert (tmp_path / "p3_evidence_gate.json").exists()
    assert (tmp_path / "p3_held_out_predictive_validation.md").exists()

