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


def test_frozen_contract_uses_observation_only_authority():
    contract = freeze_signal_contract(
        development_ids=development_task_ids(),
        held_out_ids=default_held_out_task_ids(),
    )
    assert contract["authority"] == "OBSERVATION_ONLY"
    assert contract["behavioral_authority"] == "NONE"


def test_contract_has_no_unconditional_route_identity_rule():
    contract = freeze_signal_contract(
        development_ids=development_task_ids(),
        held_out_ids=default_held_out_task_ids(),
    )
    assert "route_id == identity_governance" not in contract["prediction_logic"]
    assert "route_id == object_tracking" not in contract["prediction_logic"]


def test_threshold_origin_is_development_only():
    contract = freeze_signal_contract(
        development_ids=development_task_ids(),
        held_out_ids=default_held_out_task_ids(),
    )
    assert "development_only" in contract["threshold_origin"]


def test_prediction_does_not_include_forbidden_feature_names():
    contract = freeze_signal_contract(
        development_ids=development_task_ids(),
        held_out_ids=["task_001.json"],
    )
    prediction = score_snapshot(_snapshot(), contract)
    assert prediction["leakage_failure_count"] == 0


def test_prediction_scores_route_identity_conditionally():
    contract = freeze_signal_contract(
        development_ids=development_task_ids(),
        held_out_ids=["task_001.json"],
    )
    supported = score_snapshot(_snapshot(route_id="identity_governance"), contract)
    unsupported = score_snapshot(_snapshot(route_id="dependency_reasoning"), contract)
    assert supported["predicted_usefulness_score"] > unsupported["predicted_usefulness_score"]
    assert unsupported["predicted_useful_boolean"] is False


def test_prediction_manifest_has_no_behavioral_authority(tmp_path):
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
    text = (tmp_path / "p3_prediction_manifest.json").read_text()
    assert '"behavioral_authority": "NONE"' in text


def test_production_order_and_budget_marked_unchanged(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["production_route_order_changed"] == "NO"
    assert result["production_route_budget_changed"] == "NO"


def test_task03_hardcoding_rejected(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    contract = {**contract, "prediction_logic": "task_id == elite_cognitive_task_03"}
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["task03_memorization_detected"] is True
    assert result["p3_gate_passed"] is False


def test_all_negative_baseline_not_treated_as_success(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run("NO_OBSERVABLE_CONTRIBUTION"),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["p3_gate_passed"] is False
    assert result["failure_mode"] == "NO_HELD_OUT_POSITIVES"


def test_average_precision_not_zero_when_undefined(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    run_p3_analysis(
        raw_run=_raw_run("NO_OBSERVABLE_CONTRIBUTION"),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    text = (tmp_path / "p3_predictive_metrics.json").read_text()
    assert '"average_precision": "NOT_ESTIMABLE"' in text


def test_roc_auc_not_zero_when_undefined(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    text = (tmp_path / "p3_predictive_metrics.json").read_text()
    assert '"roc_auc": "NOT_ESTIMABLE"' in text


def test_p3_fails_without_ranking_separation(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    positive_prediction = score_snapshot(_snapshot(route_id="dependency_reasoning"), contract)
    positive_prediction["predicted_usefulness_score"] = 0.1
    positive_prediction["predicted_useful_boolean"] = False
    negative_prediction = score_snapshot(_snapshot(route_id="identity_governance", position=4), contract)
    negative_prediction["predicted_usefulness_score"] = 0.9
    negative_prediction["predicted_useful_boolean"] = True
    raw = {
        "returncode": 0,
        "timed_out": False,
        "human_report": {"Run Id": "run_test"},
        "route_manifests": [
            {
                "run_id": "run_test",
                "task_id": "task_001.json",
                "routes": [
                    {
                        "route_id": "dependency_reasoning",
                        "route_position": 3,
                        "executed": True,
                        "contribution_state": "UNIQUE_USEFUL_CONTRIBUTION",
                    },
                    {
                        "route_id": "identity_governance",
                        "route_position": 4,
                        "executed": True,
                        "contribution_state": "NO_OBSERVABLE_CONTRIBUTION",
                    },
                ],
            }
        ],
    }
    result = run_p3_analysis(
        raw_run=raw,
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[positive_prediction, negative_prediction],
        output_dir=tmp_path,
    )
    assert result["failure_mode"] == "NO_RANKING_SEPARATION"


def test_p3_fails_when_baseline_not_beaten(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["p3_gate_passed"] is False
    assert result["failure_mode"] in {"BASELINE_NOT_BEATEN", "NO_RANKING_SEPARATION"}


def test_positive_context_counts_are_reported(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["held_out_unique_positive_causal_contexts"] == 1


def test_signal_mutation_count_reported_zero_for_frozen_contract(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["signal_contract_mutation_count"] == 0


def test_route_identity_generalization_requires_positive_supported_route(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    raw = _raw_run()
    raw["route_manifests"][0]["routes"][0]["route_id"] = "dependency_reasoning"
    prediction = score_snapshot(_snapshot(route_id="dependency_reasoning"), contract)
    result = run_p3_analysis(
        raw_run=raw,
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[prediction],
        output_dir=tmp_path,
    )
    assert result["route_identity_generalization"] == "NOT_SUPPORTED"


def test_task_generalization_requires_positive_held_out_task(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run("NO_OBSERVABLE_CONTRIBUTION"),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["task_generalization"] == "NOT_SUPPORTED"


def test_prediction_authority_reported(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["prediction_authority"] == "OBSERVATION_ONLY"


def test_budget_authority_reported_runtime_budget_enforcer(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["budget_authority"] == "RuntimeBudgetEnforcer"


def test_cognitive_consumer_count_zero(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["cognitive_consumer_count"] == 0


def test_policy_patch_not_allowed(tmp_path):
    dev = development_task_ids()
    held = ["task_001.json"]
    contract = freeze_signal_contract(development_ids=dev, held_out_ids=held)
    result = run_p3_analysis(
        raw_run=_raw_run(),
        development_ids=dev,
        held_out_ids=held,
        contract=contract,
        predictions=[score_snapshot(_snapshot(), contract)],
        output_dir=tmp_path,
    )
    assert result["adaptive_policy_patch_allowed"] is False


def test_contract_lists_allowed_feature_families():
    contract = freeze_signal_contract(
        development_ids=development_task_ids(),
        held_out_ids=default_held_out_task_ids(),
    )
    names = " ".join(contract["allowed_input_features"])
    for family in ["ROUTE_IDENTITY", "STATIC_TASK", "BUDGET_CONTEXT", "STATE_SO_FAR", "PRIOR_ROUTE_STATE"]:
        assert family in names
