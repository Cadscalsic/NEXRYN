from copy import deepcopy

from runtime.claim_identity import (
    build_claim_evidence_binding,
    candidate_operation_claim_subject,
    derive_claim_id,
)
from runtime.epistemic import AcceptedEvidenceEpistemicAssessmentEngine
from runtime.epistemic.truth_candidate_engine import TruthCandidateEngine
from runtime.validation.accepted_evidence_lifecycle import AcceptedEvidenceLifecycleEngine


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
    origin = {
        "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
        "raw_evidence_id": f"raw_{accepted_evidence_id}",
        "raw_result_id": f"raw_{accepted_evidence_id}",
        "acceptance_decision_id": decision["evidence_decision_id"],
        "origin_task_execution_id": (
            f"task_execution_{source_run_id}_{selected_validation_task_id}"
        ),
        "origin_run_id": source_run_id,
        "origin_task_id": selected_validation_task_id,
        "origin_attempt_id": f"attempt_{accepted_evidence_id}",
        "origin_operation_id": producer_operation_id or accepted_evidence_id,
        "origin_lineage_fingerprint": f"origin_fp_{accepted_evidence_id}",
        "authority": "NONE",
        "behavioral_authority": "NONE",
    }
    accepted["accepted_evidence_origin"] = origin
    accepted["accepted_evidence_origin_state"] = "TASK_ORIGIN_PRESERVED"
    accepted["origin_task_execution_id"] = origin["origin_task_execution_id"]
    accepted["origin_run_id"] = origin["origin_run_id"]
    accepted["origin_task_id"] = origin["origin_task_id"]
    accepted["origin_lineage_fingerprint"] = origin["origin_lineage_fingerprint"]
    accepted["source_provenance"] = {
        "source_provenance_state": "SOURCE_PROVENANCE_BOUND",
        "producer_operation_id": producer_operation_id or accepted_evidence_id,
        "producer_component_id": producer_component_id or "component_a",
        "producer_source_type": producer_source_type or "scheduled_validation_task",
        "raw_validation_result_id": origin["raw_evidence_id"],
        "origin_task_execution_id": origin["origin_task_execution_id"],
        "origin_run_id": origin["origin_run_id"],
        "origin_task_id": origin["origin_task_id"],
        "origin_attempt_id": origin["origin_attempt_id"],
        "origin_operation_id": origin["origin_operation_id"],
        "origin_lineage_fingerprint": origin["origin_lineage_fingerprint"],
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
    current_state = AcceptedEvidenceLifecycleEngine().initialize_current_state(
        accepted
    )
    accepted["accepted_evidence_current_state"] = current_state
    accepted["current_status"] = current_state["current_status"]
    accepted["is_currently_accepted"] = current_state["is_currently_accepted"]
    accepted["current_lifecycle_decision_id"] = current_state[
        "current_lifecycle_decision_id"
    ]
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
    assert report["epistemic_lineage_state"] == "EPISTEMIC_LINEAGE_COMPLETE"
    assert report["origin_task_execution_ids"] == [
        "task_execution_run_a_elite_validation_task_31"
    ]
    assert report["supporting_evidence_lineage"][0]["raw_evidence_id"] == (
        "raw_accepted_evidence_a"
    )
    assert report["task_provenance_authority"] == "NONE"


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


def _with_current_state(evidence, *, status, currently_accepted=False):
    current_state = deepcopy(evidence["accepted_evidence_current_state"])
    current_state["current_status"] = status
    current_state["is_currently_accepted"] = currently_accepted
    current_state["superseded_by"] = (
        "replacement_evidence" if status == "SUPERSEDED" else None
    )
    current_state["fingerprint"] = AcceptedEvidenceLifecycleEngine()._fingerprint(
        current_state
    )
    updated = deepcopy(evidence)
    updated["accepted_evidence_current_state"] = current_state
    updated["current_status"] = status
    updated["is_currently_accepted"] = currently_accepted
    updated["current_lifecycle_decision_id"] = current_state[
        "current_lifecycle_decision_id"
    ]
    return updated


def test_noncurrent_lifecycle_states_are_excluded_from_epistemic_support():
    expected_reasons = {
        "UNDER_REVIEW": "DENIED_EVIDENCE_UNDER_REVIEW",
        "REVOKED": "DENIED_EVIDENCE_REVOKED",
        "INVALIDATED": "DENIED_EVIDENCE_INVALIDATED",
        "SUPERSEDED": "DENIED_EVIDENCE_SUPERSEDED",
        "REVALIDATION_REQUIRED": "DENIED_REVALIDATION_REQUIRED",
    }

    for status, reason in expected_reasons.items():
        evidence = _with_current_state(
            _accepted_evidence(
                accepted_evidence_id=f"accepted_evidence_{status.lower()}",
                source_run_id="run_a",
            ),
            status=status,
        )

        report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
            [evidence],
            claim_id=evidence["claim_id"],
        )

        assert report["epistemic_assessment_state"] == "NO_CURRENT_ADMISSIBLE_EVIDENCE"
        assert report["admitted_current_evidence_count"] == 0
        assert report["excluded_noncurrent_evidence_count"] == 1
        assert report["excluded_noncurrent_evidence"][0]["rejection_reason"] == reason
        assert report["source_coverage"]["supporting_evidence_count"] == 0


def test_claim_bound_historical_accepted_evidence_cannot_bypass_current_gate():
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_historical",
        source_run_id="run_a",
    )
    historical = deepcopy(evidence)
    historical.pop("accepted_evidence_current_state")
    historical.pop("current_status")
    historical.pop("is_currently_accepted")
    historical.pop("current_lifecycle_decision_id")

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [historical],
        claim_id=evidence["claim_id"],
    )

    assert report["epistemic_assessment_state"] == "NO_CURRENT_ADMISSIBLE_EVIDENCE"
    assert report["excluded_noncurrent_evidence"][0]["rejection_reason"] == (
        "DENIED_STALE_ACCEPTANCE_STATE"
    )


def test_assessment_binds_current_lifecycle_state_and_detects_stale_replay(tmp_path):
    lifecycle = AcceptedEvidenceLifecycleEngine(tmp_path)
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_stale",
        source_run_id="run_a",
    )
    current = lifecycle.initialize_current_state(evidence)
    evidence["accepted_evidence_current_state"] = current
    lifecycle.persist_current_state(current)
    engine = AcceptedEvidenceEpistemicAssessmentEngine(lifecycle)
    assessment = engine.assess([evidence], claim_id=evidence["claim_id"])

    assert assessment["current_lifecycle_bindings"] == [{
        "accepted_evidence_id": evidence["accepted_evidence_id"],
        "current_lifecycle_decision_id": current["current_lifecycle_decision_id"],
        "current_acceptance_decision_id": current["current_acceptance_decision_id"],
        "current_status": "ACTIVE",
        "is_currently_accepted": True,
        "current_state_fingerprint": current["fingerprint"],
    }]
    assert engine.is_epistemic_assessment_current(assessment)[
        "assessment_current_state"
    ] == "CURRENT_EPISTEMIC_ASSESSMENT"

    review = lifecycle.review_evidence(
        current,
        review_trigger="VALIDATION_RESULT_RETRACTED",
        trigger_evidence={
            "accepted_evidence_id": evidence["accepted_evidence_id"],
            "evidence_acceptance_state": "ACCEPTED",
            "source_provenance": {
                "source_provenance_state": "SOURCE_PROVENANCE_BOUND"
            },
        },
    )
    reviewed = lifecycle.current_state_from_lifecycle_decision(current, review)
    revocation = lifecycle.revoke_evidence(
        reviewed,
        review,
        revocation_reason="withdrawn",
    )
    revoked = lifecycle.current_state_from_lifecycle_decision(reviewed, revocation)
    lifecycle.persist_current_state(revoked, lifecycle_decision=revocation)

    stale = engine.is_epistemic_assessment_current(assessment)

    assert stale["assessment_current_state"] == "STALE_EPISTEMIC_ASSESSMENT"
    assert stale["current_support_available"] is False
    assert stale["truth_authority"] == "NONE"


def test_mixed_multi_evidence_excludes_revoked_item_from_current_support():
    active_a = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_active_a",
        source_run_id="run_a",
        producer_operation_id="producer_a",
        producer_component_id="component_a",
        producer_source_type="scheduled_validation_task",
    )
    revoked = _with_current_state(
        _accepted_evidence(
            accepted_evidence_id="accepted_evidence_revoked_b",
            source_run_id="run_b",
            producer_operation_id="producer_b",
            producer_component_id="component_b",
            producer_source_type="scheduled_validation_task",
        ),
        status="REVOKED",
    )
    active_c = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_active_c",
        source_run_id="run_c",
        producer_operation_id="producer_c",
        producer_component_id="component_c",
        producer_source_type="scheduled_validation_task",
    )

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [active_a, revoked, active_c],
        claim_id=active_a["claim_id"],
    )

    assert report["supporting_accepted_evidence_ids"] == [
        "accepted_evidence_active_a",
        "accepted_evidence_active_c",
    ]
    assert report["excluded_evidence_ids"] == ["accepted_evidence_revoked_b"]
    assert report["supporting_evidence_count"] == 2
    assert report["source_coverage"]["supporting_evidence_count"] == 2
    assert report["independent_supporting_source_count"] == 2


def test_current_gate_rejects_identity_and_fingerprint_attacks():
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_attacked",
        source_run_id="run_a",
    )
    cross = deepcopy(evidence)
    cross["accepted_evidence_current_state"] = deepcopy(
        evidence["accepted_evidence_current_state"]
    )
    cross["accepted_evidence_current_state"]["accepted_evidence_id"] = "other"
    cross["accepted_evidence_current_state"]["evidence_id"] = "other"
    cross["accepted_evidence_current_state"]["fingerprint"] = (
        AcceptedEvidenceLifecycleEngine()._fingerprint(
            cross["accepted_evidence_current_state"]
        )
    )
    corrupted = deepcopy(evidence)
    corrupted["accepted_evidence_current_state"] = deepcopy(
        evidence["accepted_evidence_current_state"]
    )
    corrupted["accepted_evidence_current_state"]["fingerprint"] = "corrupted"

    report = AcceptedEvidenceEpistemicAssessmentEngine().assess(
        [cross, corrupted],
        claim_id=evidence["claim_id"],
    )

    reasons = [
        row["rejection_reason"] for row in report["excluded_noncurrent_evidence"]
    ]
    assert "DENIED_EVIDENCE_IDENTITY_MISMATCH" in reasons
    assert "DENIED_CURRENT_LIFECYCLE_UNVERIFIED" in reasons


def test_persisted_assessment_reloads_as_current_for_truth_ingestion(tmp_path):
    lifecycle = AcceptedEvidenceLifecycleEngine(tmp_path / "state")
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_persisted",
        source_run_id="run_a",
        producer_operation_id="producer_a",
        producer_component_id="component_a",
        producer_source_type="scheduled_validation_task",
    )
    current = lifecycle.initialize_current_state(evidence)
    evidence["accepted_evidence_current_state"] = current
    lifecycle.persist_current_state(current)
    assessment_engine = AcceptedEvidenceEpistemicAssessmentEngine(lifecycle)
    assessment = assessment_engine.assess([evidence], claim_id=evidence["claim_id"])
    path = tmp_path / "assessment.json"
    path.write_text(__import__("json").dumps(assessment), encoding="utf-8")
    reloaded = __import__("json").loads(path.read_text(encoding="utf-8"))
    truth_engine = TruthCandidateEngine()
    truth_engine.accepted_evidence_assessment_engine = assessment_engine

    admission = truth_engine.admit_current_epistemic_assessment_for_truth(
        reloaded,
        expected_claim_id=evidence["claim_id"],
    )
    coverage = truth_engine._source_coverage({
        "claim_id": evidence["claim_id"],
        "accepted_evidence_epistemic_assessment": reloaded,
    })

    assert admission["truth_facing_assessment_admission_state"] == (
        "ASSESSMENT_CURRENT_AND_ADMISSIBLE"
    )
    assert admission["truth_authority"] == "NONE"
    assert coverage["accepted_evidence_count"] == 1


def test_truth_ingestion_denies_persisted_assessment_after_revocation(tmp_path):
    lifecycle = AcceptedEvidenceLifecycleEngine(tmp_path / "state")
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_truth_stale",
        source_run_id="run_a",
    )
    current = lifecycle.initialize_current_state(evidence)
    evidence["accepted_evidence_current_state"] = current
    lifecycle.persist_current_state(current)
    assessment_engine = AcceptedEvidenceEpistemicAssessmentEngine(lifecycle)
    assessment = assessment_engine.assess([evidence], claim_id=evidence["claim_id"])
    review = lifecycle.review_evidence(
        current,
        review_trigger="VALIDATION_RESULT_RETRACTED",
        trigger_evidence={
            "accepted_evidence_id": evidence["accepted_evidence_id"],
            "evidence_acceptance_state": "ACCEPTED",
            "source_provenance": {
                "source_provenance_state": "SOURCE_PROVENANCE_BOUND"
            },
        },
    )
    reviewed = lifecycle.current_state_from_lifecycle_decision(current, review)
    revocation = lifecycle.revoke_evidence(
        reviewed,
        review,
        revocation_reason="withdrawn",
    )
    lifecycle.persist_current_state(
        lifecycle.current_state_from_lifecycle_decision(reviewed, revocation),
        lifecycle_decision=revocation,
    )
    truth_engine = TruthCandidateEngine()
    truth_engine.accepted_evidence_assessment_engine = assessment_engine

    admission = truth_engine.admit_current_epistemic_assessment_for_truth(
        assessment,
        expected_claim_id=evidence["claim_id"],
    )
    coverage = truth_engine._source_coverage({
        "claim_id": evidence["claim_id"],
        "accepted_evidence_epistemic_assessment": assessment,
    })

    assert admission["truth_facing_assessment_admission_state"] == (
        "TRUTH_FACING_ASSESSMENT_ADMISSION_DENIED"
    )
    assert "STALE_EPISTEMIC_ASSESSMENT" in admission["admission_failures"]
    assert coverage["current_proven_independent_source_count"] == 0


def test_truth_ingestion_denies_corrupted_persisted_assessment_fingerprint(tmp_path):
    lifecycle = AcceptedEvidenceLifecycleEngine(tmp_path / "state")
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_corrupted_assessment",
        source_run_id="run_a",
    )
    current = lifecycle.initialize_current_state(evidence)
    evidence["accepted_evidence_current_state"] = current
    lifecycle.persist_current_state(current)
    assessment_engine = AcceptedEvidenceEpistemicAssessmentEngine(lifecycle)
    assessment = assessment_engine.assess([evidence], claim_id=evidence["claim_id"])
    assessment["supporting_evidence_count"] = 99
    truth_engine = TruthCandidateEngine()
    truth_engine.accepted_evidence_assessment_engine = assessment_engine

    admission = truth_engine.admit_current_epistemic_assessment_for_truth(
        assessment,
        expected_claim_id=evidence["claim_id"],
    )

    assert admission["truth_facing_assessment_admission_state"] == (
        "TRUTH_FACING_ASSESSMENT_ADMISSION_DENIED"
    )
    assert "assessment_fingerprint_invalid" in admission[
        "currentness_validation"
    ]["integrity_failures"]


def test_truth_ingestion_denies_cross_claim_persisted_assessment(tmp_path):
    lifecycle = AcceptedEvidenceLifecycleEngine(tmp_path / "state")
    evidence = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_cross_claim",
        source_run_id="run_a",
    )
    current = lifecycle.initialize_current_state(evidence)
    evidence["accepted_evidence_current_state"] = current
    lifecycle.persist_current_state(current)
    assessment_engine = AcceptedEvidenceEpistemicAssessmentEngine(lifecycle)
    assessment = assessment_engine.assess([evidence], claim_id=evidence["claim_id"])
    truth_engine = TruthCandidateEngine()
    truth_engine.accepted_evidence_assessment_engine = assessment_engine

    admission = truth_engine.admit_current_epistemic_assessment_for_truth(
        assessment,
        expected_claim_id="claim_sha256_other",
    )

    assert admission["truth_facing_assessment_admission_state"] == (
        "TRUTH_FACING_ASSESSMENT_ADMISSION_DENIED"
    )
    assert "ASSESSMENT_CLAIM_IDENTITY_MISMATCH" in admission["admission_failures"]


def test_truth_ingestion_denies_cross_evidence_binding_substitution(tmp_path):
    lifecycle = AcceptedEvidenceLifecycleEngine(tmp_path / "state")
    first = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_binding_a",
        source_run_id="run_a",
    )
    second = _accepted_evidence(
        accepted_evidence_id="accepted_evidence_binding_b",
        source_run_id="run_b",
    )
    first_current = lifecycle.initialize_current_state(first)
    second_current = lifecycle.initialize_current_state(second)
    first["accepted_evidence_current_state"] = first_current
    second["accepted_evidence_current_state"] = second_current
    lifecycle.persist_current_state(first_current)
    lifecycle.persist_current_state(second_current)
    assessment_engine = AcceptedEvidenceEpistemicAssessmentEngine(lifecycle)
    assessment = assessment_engine.assess([first], claim_id=first["claim_id"])
    assessment["current_lifecycle_bindings"][0] = {
        "accepted_evidence_id": second["accepted_evidence_id"],
        "current_lifecycle_decision_id": second_current[
            "current_lifecycle_decision_id"
        ],
        "current_acceptance_decision_id": second_current[
            "current_acceptance_decision_id"
        ],
        "current_status": second_current["current_status"],
        "is_currently_accepted": second_current["is_currently_accepted"],
        "current_state_fingerprint": second_current["fingerprint"],
    }
    assessment["assessment_fingerprint"] = (
        assessment_engine._assessment_fingerprint(assessment)
    )
    truth_engine = TruthCandidateEngine()
    truth_engine.accepted_evidence_assessment_engine = assessment_engine

    admission = truth_engine.admit_current_epistemic_assessment_for_truth(
        assessment,
        expected_claim_id=first["claim_id"],
    )

    assert admission["truth_facing_assessment_admission_state"] == (
        "TRUTH_FACING_ASSESSMENT_ADMISSION_DENIED"
    )
    assert admission["currentness_validation"]["stale_lifecycle_bindings"][0][
        "stale_reason"
    ] == "assessment_evidence_identity_mismatch"
