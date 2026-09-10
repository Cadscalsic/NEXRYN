from runtime.experiments.capability_qualification_lifecycle_verification import (
    run_capability_qualification_lifecycle_verification,
)


def test_capability_qualification_lifecycle_verification_artifacts(tmp_path):
    result = run_capability_qualification_lifecycle_verification(output_dir=tmp_path)

    required = {
        "capability_qualification_lifecycle_trace.json",
        "qualification_review_decision.json",
        "qualification_invalidation_decision.json",
        "qualification_revalidation_decision.json",
        "current_qualification_state.json",
        "qualification_history.json",
        "authority_audit.json",
        "attack_test_results.json",
        "regression_results.json",
        "natural_runtime_verification.json",
        "full_invalidation_control.json",
        "restoration_control.json",
        "capability_qualification_lifecycle_closure_decision.json",
        "capability_qualification_lifecycle_system_fingerprint.json",
    }

    assert {path.name for path in tmp_path.iterdir()} >= required
    assert result["closure_decision"]["status"] == (
        "CLOSED_FOR_CAPABILITY_QUALIFICATION_LIFECYCLE"
    )
    assert result["attack_results"]["attack_test_count"] == 30
    assert result["attack_results"]["attack_test_failure_count"] == 0
    assert result["synthetic_lifecycle"]["current_state"][
        "current_qualification_level"
    ] == "RUNTIME_REACHABLE"
    assert result["full_invalidation"]["current_state"][
        "qualification_status"
    ] == "INVALIDATED"
    assert result["restoration"]["automatic_restoration_before_revalidation"] is False
