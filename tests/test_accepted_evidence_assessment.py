from copy import deepcopy

from runtime.claim_identity import (
    build_claim_evidence_binding,
    candidate_operation_claim_subject,
    derive_claim_id,
)
from runtime.epistemic import AcceptedEvidenceEpistemicAssessmentEngine


def _accepted_evidence(
    *,
    accepted_evidence_id: str,
    source_run_id: str,
    selected_validation_task_id: str = "elite_validation_task_31",
    producer_operation_id: str | None = None,
    producer_component_id: str | None = None,
    producer_source_type: str | None = None,
    source_lineage: list[str] | None = None,
    direction: str = "SUPPORTING",
):
    subject = candidate_operation_claim_subject(
        subject_ref="semantic_to_transformation_compiler_0",
        operation="replace_color",
    )
    claim_id = derive_claim_id(subject)
    plan = {
        "plan_id": f"evidence_plan_{accepted_evidence_id}",
        "claim_id": claim_id,
        "claim_subject": subject.canonical_payload(),
        "target_candidate": "semantic_to_transformation_compiler_0",
        "target_operation": "replace_color",
    }
    decision = {
        "plan_id": plan["plan_id"],
        "evidence_decision_id": f"evidence_decision_{accepted_evidence_id}",
        "claim_id": claim_id,
        "claim_subject": subject.canonical_payload(),
        "target_candidate": "semantic_to_transformation_compiler_0",
        "target_operation": "replace_color",
        "evidence_direction": direction,
        "evidence_acceptance_state": "ACCEPTED",
    }
    accepted = {
        "accepted_evidence_id": accepted_evidence_id,
        "plan_id": plan["plan_id"],
        "evidence_decision_id": decision["evidence_decision_id"],
        "claim_id": claim_id,
        "claim_subject": subject.canonical_payload(),
        "source_run_id": source_run_id,
        "selected_validation_task_id": selected_validation_task_id,
        "evaluation_contract_id": "validation_evidence_evaluation_contract_1",
        "required_evidence": "cross_source_consensus_evidence",
        "target_candidate": "semantic_to_transformation_compiler_0",
        "target_operation": "replace_color",
        "evidence_direction": direction,
        "evidence_acceptance_state": "ACCEPTED",
        "truth_authority": "NONE",
        "trust_authority": "NONE",
        "graduation_authority": "NONE",
        "candidate_execution_authority": "NONE",
    }
    if producer_operation_id:
        accepted["producer_operation_id"] = producer_operation_id
    if producer_component_id:
        accepted["producer_component_id"] = producer_component_id
    if producer_source_type:
        accepted["producer_source_type"] = producer_source_type
    if source_lineage:
        accepted["source_lineage"] = source_lineage
    binding = build_claim_evidence_binding(
        claim_subject=accepted["claim_subject"],
        evidence_plan=plan,
        evidence_decision=decision,
        accepted_evidence=accepted,
    )
    accepted["claim_evidence_binding"] = binding
    accepted["claim_evidence_binding_id"] = binding["claim_evidence_binding_id"]
    accepted["claim_evidence_binding_state"] = "BOUND"
    return accepted


def test_bound_accepted_evidence_reaches_epistemic_assessment_not_truth():
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_a",
        source_run_id="run_a",
    )

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [evidence],
        claim_id=evidence["claim_id"],
        assessment_run_id="run_e2",
    )

    assert report["claim_id"] == evidence["claim_id"]
    assert report["accepted_evidence_ids"] == ["accepted_evidence_a"]
    assert report["epistemic_assessment_state"] == (
        "INSUFFICIENT_FOR_TRUTH_CANDIDACY"
    )
    assert report["truth_candidate_id"] == "NOT_REACHED"
    assert report["truth_id"] == "NOT_REACHED"
    assert report["knowledge_object_id"] == "NOT_REACHED"
    assert report["authority"]["truth_commitment"] == "NONE"
    assert report["authority"]["knowledge_projection"] == "NONE"
    assert report["authority"]["budget"] == "NONE"


def test_wrong_claim_evidence_is_rejected_from_assessment():
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_a",
        source_run_id="run_a",
    )

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [evidence],
        claim_id="claim_sha256_wrong",
    )

    assert report["bound_accepted_evidence_count"] == 0
    assert report["rejected_evidence"][0]["rejection_reason"] == "wrong_claim"
    assert report["epistemic_assessment_state"] == "NO_BOUND_ACCEPTED_EVIDENCE"


def test_duplicate_evidence_does_not_inflate_independent_support():
    first = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_a",
        source_run_id="run_a",
        producer_operation_id="producer_a",
        producer_component_id="component_a",
        producer_source_type="scheduled_validation_task",
    )
    duplicate = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_b",
        source_run_id="run_a",
        producer_operation_id="producer_a",
        producer_component_id="component_a",
        producer_source_type="scheduled_validation_task",
    )

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [first, duplicate],
        claim_id=first["claim_id"],
    )

    assert report["supporting_evidence_count"] == 2
    assert report["independent_supporting_source_count"] == 1
    assert report["duplicate_supporting_evidence_count"] == 1
    assert report["evidence_diversity_state"] == "DUPLICATES_DEDUPED"


def test_weak_run_task_tuple_does_not_count_as_proven_independence():
    first = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_a",
        source_run_id="run_a",
    )
    second = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_b",
        source_run_id="run_b",
        selected_validation_task_id="elite_validation_task_32",
    )

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [first, second],
        claim_id=first["claim_id"],
    )

    assert report["supporting_evidence_count"] == 2
    assert report["independent_supporting_source_count"] == 0
    assert report["evidence_diversity_state"] == (
        "UNKNOWN_SOURCE_PROVENANCE_FAIL_CLOSED"
    )


def test_historical_pre_e1_unbound_evidence_is_classified_not_upgraded():
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_a",
        source_run_id="run_a",
    )
    historical = deepcopy(evidence)
    historical.pop("claim_evidence_binding")
    historical.pop("claim_evidence_binding_id")
    historical["claim_evidence_binding_state"] = "NOT_AVAILABLE"

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [historical],
        claim_id=evidence["claim_id"],
    )

    assert report["bound_accepted_evidence_count"] == 0
    assert report["historical_unbound_evidence"] == [{
        "accepted_evidence_id": "accepted_evidence_a",
        "classification": "HISTORICAL_PRE_E1_UNBOUND",
        "claim_id": evidence["claim_id"],
    }]


def test_contradicting_accepted_evidence_blocks_promotion_readiness():
    supporting = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_a",
        source_run_id="run_a",
    )
    contradicting = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_b",
        source_run_id="run_b",
        direction="CONTRADICTING",
    )

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [supporting, contradicting],
        claim_id=supporting["claim_id"],
    )

    assert report["contradicting_accepted_evidence_ids"] == ["accepted_evidence_b"]
    assert report["epistemic_assessment_state"] == "CONTRADICTORY_EVIDENCE_PRESENT"
