from runtime.experiments.integrated_capability_qualification_verification import (
    run_integrated_capability_qualification_verification,
)


def test_integrated_capability_qualification_verification_artifacts(tmp_path):
    result = run_integrated_capability_qualification_verification(output_dir=tmp_path)

    required = {
        "capability_qualification_system_fingerprint.json",
        "capability_qualification_forensic_map.json",
        "capability_identity_contract.json",
        "capability_qualification_authority_map.json",
        "capability_qualification_level_contract.json",
        "capability_evidence_binding_map.json",
        "capability_source_independence_audit.json",
        "capability_qualification_attack_results.json",
        "capability_qualification_integration_trace.json",
        "capability_qualification_runtime_verification.json",
        "capability_qualification_regression_results.json",
        "capability_qualification_closure_decision.json",
        "integrated_capability_qualification_report.md",
    }

    assert {path.name for path in tmp_path.iterdir()} >= required
    assert result["closure_decision"][
        "integrated_capability_qualification_status"
    ] == "CLOSED"
    assert result["runtime_verification"]["real_runtime_qualification_observed"] is True
    assert (
        result["runtime_verification"]["real_runtime_denied_promotion_observed"]
        is True
    )
    assert result["runtime_verification"][
        "reproducibly_supported_runtime_case"
    ] == "NOT_OBSERVED"
    assert result["integration_trace"]["integration_trace_complete"] is True
    assert result["attack_results"]["attack_test_count"] == 25
    assert result["attack_results"]["attack_test_failure_count"] == 0
