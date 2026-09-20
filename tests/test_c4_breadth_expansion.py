from pathlib import Path

from runtime.capability_intelligence.integrated_capability_qualification import (
    capability_id_for_subject,
)
from runtime.experiments.c4_breadth_expansion import (
    capability_breadth,
    classify_context_candidate,
    context_identity_contract,
    development_priority,
    operation_breadth,
    run_breadth_expansion,
    source_replication_readiness,
)


def _candidate(index=1, *, operation="fill_center", sources=2, contexts=1):
    subject = {
        "schema_version": "1.0",
        "capability_name": f"{operation}_capability",
        "operation": operation,
        "domain": "arc_grid_transformation",
        "qualifiers": {"validation_context": f"{operation}_context_a"},
    }
    return {
        "candidate_id": f"candidate_{index}",
        "capability_id": capability_id_for_subject(subject),
        "capability_subject": subject,
        "operation": operation,
        "qualification_claim_id": f"claim_{index}",
        "qualification_level": "REPRODUCIBLY_SUPPORTED",
        "prequalification_state": "C5_NOT_READY",
        "capability_binding_state": "BOUND",
        "claim_binding_state": "BOUND",
        "operation_binding_state": "BOUND",
        "causal_validation_reachable": True,
        "counterfactual_state": "COUNTERFACTUAL_READY",
        "independent_causal_source_count": sources,
        "observed_context_count": contexts,
        "canonical_source_identities": [f"source_{index}_{i}" for i in range(sources)],
        "missing_requirements": ["second_exact_subject_context_not_demonstrated"],
        "causal_method": "CONTROLLED_TRANSFORMATION_EFFECT",
        "causal_estimand": "treatment_score - control_score",
    }


def test_context_identity_contract_separates_subject_identity_from_context():
    contract = context_identity_contract()

    assert contract["exact_subject_identity"] == [
        "capability_id",
        "capability_operation",
        "qualification_claim_id",
    ]
    assert "new_run_only" in contract["forbidden_context_variation"]


def test_new_context_rejected_when_qualifier_changes_capability_id():
    existing = _candidate()
    proposed_subject = {
        **existing["capability_subject"],
        "qualifiers": {"validation_context": "fill_center_context_b"},
    }

    result = classify_context_candidate(
        existing,
        {
            "context_id": "fill_center_context_b",
            "operation": "fill_center",
            "geometry": "larger_grid",
            "object_topology": "different_enclosure",
            "causal_challenge": "same_fill_center_larger_enclosure",
            "treatment": "fill_center",
            "control": "operation_disabled",
            "causal_variation": "structural",
            "capability_subject": proposed_subject,
        },
    )

    assert result["classification"] == "REJECTED"
    assert "capability_id_not_preserved" in result["rejection_reasons"]


def test_cosmetic_context_variation_is_rejected():
    existing = _candidate()

    result = classify_context_candidate(
        existing,
        {
            "context_id": "cosmetic",
            "operation": "fill_center",
            "geometry": existing["observed_context_count"],
            "object_topology": "fill_center_context_a",
            "causal_challenge": "fill_center",
            "treatment": "CONTROLLED_TRANSFORMATION_EFFECT",
            "control": "treatment_score - control_score",
            "causal_variation": "cosmetic",
            "capability_subject": existing["capability_subject"],
        },
    )

    assert "same_context_replay" in result["rejection_reasons"]
    assert "cosmetic_variation_only" in result["rejection_reasons"]


def test_source_readiness_does_not_count_new_task_as_source():
    rows = source_replication_readiness([_candidate(sources=1)])

    assert rows[0]["second_source_readiness"] == "REQUIRES_NEW_VALIDATION_CONTEXT"
    assert "task/run/evidence" in rows[0]["source_provenance_requirement"]


def test_breadth_counting_uses_capability_and_operation_distinctness():
    matrix = [
        _candidate(1, operation="fill_center"),
        _candidate(2, operation="outline_border", sources=1),
        _candidate(3, operation="replace_color", sources=1),
    ]

    assert capability_breadth(matrix)["plausible_capability_family_count"] == 3
    assert operation_breadth(matrix)["unique_operation_count"] == 3


def test_development_priority_is_structural_not_only_c4_success():
    matrix = [
        _candidate(1, operation="fill_center", sources=2),
        _candidate(2, operation="outline_border", sources=1),
    ]

    ranked = development_priority(matrix)

    assert {item["candidate_id"] for item in ranked} == {"candidate_1", "candidate_2"}
    assert all("prior positive outcome" not in item["rationale"] for item in ranked)


def test_run_breadth_expansion_preserves_no_freeze_and_no_c5_claim(tmp_path: Path):
    result = run_breadth_expansion(output_root=tmp_path)
    output_dir = Path(result["output_dir"])

    assert output_dir.is_relative_to(tmp_path)
    assert result["c5_target_set_frozen"] is False
    assert result["c5_campaign_executed"] is False
    assert result["c5_authorized_for_claim"] is False
    assert result["c4_development_attempt_count"] == 0
    assert (output_dir / "20_c4_breadth_expansion_report.md").exists()
