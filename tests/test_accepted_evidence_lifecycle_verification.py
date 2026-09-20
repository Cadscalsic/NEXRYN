from runtime.experiments.accepted_evidence_lifecycle_verification import (
    run_accepted_evidence_lifecycle_verification,
)


def test_accepted_evidence_lifecycle_verification_artifacts(tmp_path):
    result = run_accepted_evidence_lifecycle_verification(output_dir=tmp_path)

    required = {
        "accepted_evidence_authority_map.json",
        "accepted_evidence_lifecycle_trace.json",
        "evidence_review_decision.json",
        "evidence_revocation_decision.json",
        "evidence_invalidation_decision.json",
        "evidence_supersession_decision.json",
        "current_evidence_state.json",
        "evidence_history.json",
        "qualification_trigger_integration_trace.json",
        "downstream_consumer_audit.json",
        "authority_audit.json",
        "attack_test_results.json",
        "regression_results.json",
        "natural_runtime_verification.json",
    }
    assert {path.name for path in tmp_path.iterdir()} >= required
    assert result["closure_decision"]["status"] == (
        "CLOSED_FOR_ACCEPTED_EVIDENCE_LIFECYCLE"
    )
    assert result["attack_results"]["attack_test_count"] == 35
    assert result["attack_results"]["attack_test_failure_count"] == 0
    assert result["false_evidence_revocation_count"] == 0
    assert result["false_evidence_review_count"] == 0
