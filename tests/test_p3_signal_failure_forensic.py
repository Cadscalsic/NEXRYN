import pytest

from runtime.experiments.p3_signal_failure_forensic import (
    DEFAULT_DEVELOPMENT_DATASET,
    DEFAULT_P3_DIR,
    run_failure_forensic,
)


@pytest.fixture(scope="module")
def forensic_report(tmp_path_factory):
    return run_failure_forensic(
        p3_dir=DEFAULT_P3_DIR,
        development_dataset_path=DEFAULT_DEVELOPMENT_DATASET,
        output_dir=tmp_path_factory.mktemp("p3_signal_failure_forensic"),
    )


def test_exact_v1_contract_reconstruction(forensic_report):
    reconstruction = forensic_report["v1_contract_reconstruction"]
    assert reconstruction["signal_contract_id"] == "p3_signal_contract_91e1d9966b4cb6cd"
    assert reconstruction["frozen_feature_count"] == 9


def test_frozen_threshold_preserved(forensic_report):
    assert forensic_report["v1_contract_reconstruction"]["threshold"] == 0.7
    assert forensic_report["threshold_geometry"]["frozen_threshold"] == 0.7


def test_consumed_held_out_tasks_not_fresh_validation(forensic_report):
    assert forensic_report["authority_audit"]["held_out_evidence_state"] == "CONSUMED_VALIDATION_EVIDENCE"
    assert forensic_report["candidate_v2_eligibility"]["consumed_held_out_may_validate_v2"] is False


def test_rowwise_candidate_baseline_comparison(forensic_report):
    comparison = forensic_report["incremental_information_result"]
    assert comparison["binary_decisions_changed"] == 0
    assert comparison["ordering_changed"] == 0


def test_false_positive_extraction(forensic_report):
    analysis = forensic_report["false_positive_analysis"]
    assert analysis["false_positive_count"] == 38
    assert analysis["clusters"]["by_route_id"] == {"identity_governance": 19, "object_tracking": 19}


def test_true_positive_extraction(forensic_report):
    analysis = forensic_report["true_positive_analysis"]
    assert analysis["true_positive_count"] == 2
    assert {row["route_id"] for row in analysis["records"]} == {"identity_governance", "object_tracking"}


def test_false_negative_count_zero(forensic_report):
    assert forensic_report["false_negative_analysis"]["false_negative_count"] == 0


def test_within_route_discrimination_calculated(forensic_report):
    assert forensic_report["within_route_discrimination"]["overall"] == "WITHIN_ROUTE_DISCRIMINATION_ABSENT"


def test_within_task_discrimination_calculated(forensic_report):
    task020 = forensic_report["within_task_discrimination"]["task_020"]
    assert task020["actual_useful_routes_ranked_above_non_useful"] is True


def test_feature_variation_global_and_within_route(forensic_report):
    variation = forensic_report["feature_variation"]["ROUTE_IDENTITY.route_id"]
    assert variation["global_unique_values"] == 4
    assert variation["within_route_unique_values"]["identity_governance"] == 1


def test_redundancy_analysis_present(forensic_report):
    redundancy = forensic_report["feature_redundancy"]
    assert redundancy["non_route_feature_redundancy"] == "SUPPORTED_PRIMARY"


def test_development_heldout_distribution_comparison(forensic_report):
    assert "STATIC_TASK.object_count" in forensic_report["distribution_shift"]["features"]


def test_no_threshold_optimization(forensic_report):
    assert forensic_report["threshold_geometry"]["optimization_performed"] is False
    assert forensic_report["threshold_root_cause_decision"] == "NOT_PRIMARY_THRESHOLD_ROOT_CAUSE"


def test_no_feature_selection_or_refit_authority(forensic_report):
    assert forensic_report["authority_audit"]["forensic_tool_authority"] == "NONE"
    assert forensic_report["authority_audit"]["behavioral_authority"] == "NONE"


def test_held_out_hypotheses_labeled_correctly(forensic_report):
    eligibility = forensic_report["candidate_v2_eligibility"]
    assert eligibility["held_out_inspired_hypothesis_count"] == 1
    assert eligibility["new_never_used_held_out_set_required"] is True


def test_v2_not_justified_from_held_out_evidence(forensic_report):
    eligibility = forensic_report["candidate_v2_eligibility"]
    assert eligibility["scientifically_justified_now"] is False
    assert eligibility["classification"] == "V2_REQUIRES_NEW_SIGNAL_INSTRUMENTATION"


def test_p2_remains_distinct_from_p3(forensic_report):
    assert forensic_report["p2_status"] == "P2_ASSOCIATION_VALID"
    assert forensic_report["p3_v1_status"] == "P3_PREDICTOR_FAILED"


def test_p4_remains_blocked(forensic_report):
    assert forensic_report["p4_decision"]["p4_allowed"] is False
    assert forensic_report["p4_decision"]["adaptive_policy_patch_allowed"] is False


def test_cognitive_consumer_count_zero(forensic_report):
    assert forensic_report["authority_audit"]["cognitive_consumer_count"] == 0


def test_production_behavior_unchanged(forensic_report):
    assert forensic_report["authority_audit"]["production_behavior_changed"] == "NO"
