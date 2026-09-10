from runtime.experiments.governed_evidence_acceptance_verification import (
    run_governed_acceptance_verification,
)


def test_governed_acceptance_verification_writes_closure_artifacts(tmp_path):
    result = run_governed_acceptance_verification(output_dir=tmp_path)

    required_artifacts = {
        "evidence_acceptance_system_fingerprint.json",
        "evidence_acceptance_forensic_map.json",
        "evidence_acceptance_authority_map.json",
        "evidence_acceptance_identity_contract.json",
        "evidence_acceptance_provenance_contract.json",
        "evidence_acceptance_attack_results.json",
        "evidence_acceptance_integration_trace.json",
        "evidence_acceptance_runtime_verification.json",
        "evidence_acceptance_regression_results.json",
        "evidence_acceptance_closure_decision.json",
        "governed_evidence_acceptance_report.md",
    }

    assert {path.name for path in tmp_path.iterdir()} >= required_artifacts
    assert result["closure_decision"]["governed_evidence_acceptance_status"] == "CLOSED"
    assert result["closure_decision"]["post_repair_evidence_level"] == (
        "CAUSALLY_DEMONSTRATED"
    )
    assert (
        result["runtime_verification"]["real_runtime_acceptance_observed"] is True
    )
    assert (
        result["runtime_verification"][
            "real_runtime_rejection_or_non_acceptance_observed"
        ]
        is True
    )
    assert result["integration_trace"]["integration_trace_complete"] is True
    assert result["attack_results"]["attack_test_count"] == 20
    assert result["attack_results"]["attack_test_failure_count"] == 0
