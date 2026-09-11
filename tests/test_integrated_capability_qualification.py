from copy import deepcopy

import pytest

from runtime.capability_intelligence.integrated_capability_qualification import (
    CapabilityQualificationLevel,
    CapabilitySubject,
    IntegratedCapabilityQualificationEngine,
    capability_id_for_subject,
)


def _subject(**overrides):
    data = {
        "capability_name": "replace_color_capability",
        "operation": "replace_color",
        "domain": "Color",
    }
    data.update(overrides)
    return CapabilitySubject(**data)


def _accepted(
    evidence_id: str,
    *,
    subject=None,
    claim_id: str = "claim_replace_color",
    source: str = "source_a",
    run_id: str = "run_a",
    task_id: str = "task_a",
    causal: bool = False,
):
    capability_subject = subject or _subject()
    capability_id = capability_id_for_subject(capability_subject)
    item = {
        "accepted_evidence_id": evidence_id,
        "evidence_acceptance_state": "ACCEPTED",
        "evidence_decision_id": f"decision_{evidence_id}",
        "claim_id": claim_id,
        "claim_evidence_binding_state": "BOUND",
        "claim_evidence_binding": {
            "claim_id": claim_id,
            "accepted_evidence_id": evidence_id,
        },
        "capability_id": capability_id,
        "target_operation": capability_subject.canonical_payload()["operation"],
        "evidence_direction": "SUPPORTING",
        "producer_operation_id": source,
        "producer_component_id": "validation_task_execution_pipeline",
        "producer_source_type": "scheduled_validation_task",
        "source_lineage": [source],
        "source_run_id": run_id,
        "selected_validation_task_id": task_id,
        "source_provenance": {
            "source_provenance_state": "SOURCE_PROVENANCE_BOUND",
            "producer_operation_id": source,
            "producer_component_id": "validation_task_execution_pipeline",
            "producer_source_type": "scheduled_validation_task",
            "source_lineage": [source],
            "run_id": run_id,
            "task_id": task_id,
            "raw_validation_result_id": f"raw_{evidence_id}",
            "origin_task_execution_id": f"task_execution_{run_id}_{task_id}",
            "origin_run_id": run_id,
            "origin_task_id": task_id,
            "origin_attempt_id": f"attempt_{evidence_id}",
            "origin_operation_id": source,
            "origin_lineage_fingerprint": f"origin_fp_{evidence_id}",
        },
        "accepted_evidence_origin": {
            "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
            "raw_evidence_id": f"raw_{evidence_id}",
            "raw_result_id": f"raw_{evidence_id}",
            "acceptance_decision_id": f"decision_{evidence_id}",
            "origin_task_execution_id": f"task_execution_{run_id}_{task_id}",
            "origin_run_id": run_id,
            "origin_task_id": task_id,
            "origin_attempt_id": f"attempt_{evidence_id}",
            "origin_operation_id": source,
            "origin_lineage_fingerprint": f"origin_fp_{evidence_id}",
            "authority": "NONE",
            "behavioral_authority": "NONE",
        },
        "accepted_evidence_origin_state": "TASK_ORIGIN_PRESERVED",
        "capability_causal_support_state": (
            "CAUSALLY_SUPPORTED" if causal else "OBSERVED_ONLY"
        ),
    }
    return item


def _decision(level, evidence, **kwargs):
    return IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        evidence,
        requested_level=level,
        architecture_present=kwargs.pop("architecture_present", True),
        runtime_reachable=kwargs.pop("runtime_reachable", True),
        **kwargs,
    )["qualification_decision"]


def test_same_capability_subject_has_stable_capability_id():
    assert capability_id_for_subject(_subject()) == capability_id_for_subject(_subject())


def test_different_capability_subject_has_different_capability_id():
    assert capability_id_for_subject(_subject()) != capability_id_for_subject(
        _subject(operation="rotate")
    )


def test_same_capability_different_evidence_keeps_same_capability_id():
    first = _accepted("accepted_a")
    second = _accepted("accepted_b", source="source_b")
    assert first["capability_id"] == second["capability_id"]


def test_same_evidence_different_capability_fails_binding():
    evidence = _accepted("accepted_a")
    decision = IntegratedCapabilityQualificationEngine().decide(
        _subject(operation="rotate"),
        [evidence],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )["qualification_decision"]
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert "some_evidence_rejected" in decision["promotion_failures"]


def test_valid_architecturally_present_state():
    decision = _decision(
        CapabilityQualificationLevel.ARCHITECTURALLY_PRESENT,
        [],
        runtime_reachable=False,
    )
    assert decision["decision_state"] == "PROMOTION_GRANTED"
    assert decision["granted_level"] == "ARCHITECTURALLY_PRESENT"


def test_runtime_reachability_without_observation_does_not_grant_observed():
    decision = _decision(CapabilityQualificationLevel.OPERATIONALLY_OBSERVED, [])
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert "accepted_evidence_missing" in decision["promotion_failures"]


def test_observation_without_causality_does_not_grant_causal_level():
    decision = _decision(
        CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        [_accepted("accepted_a")],
    )
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert "causal_support_not_established" in decision["promotion_failures"]


def test_causality_without_reproducibility_does_not_grant_reproducible_level():
    decision = _decision(
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        [_accepted("accepted_a", causal=True)],
    )
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert "independent_reproducibility_not_established" in decision["promotion_failures"]


def test_reproducibility_with_insufficient_independent_sources_fails_closed():
    first = _accepted("accepted_a", source="source_a", causal=True)
    second = _accepted("accepted_b", source="source_a", run_id="run_b", causal=True)
    decision = _decision(
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        [first, second],
    )
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert decision["independent_source_count"] == 1


def test_valid_reproducible_support():
    decision = _decision(
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        [
            _accepted("accepted_a", source="source_a", causal=True),
            _accepted("accepted_b", source="source_b", causal=True),
        ],
    )
    assert decision["decision_state"] == "PROMOTION_GRANTED"
    assert decision["granted_level"] == "REPRODUCIBLY_SUPPORTED"
    assert decision["independent_source_count"] == 2


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        (lambda e: e.update({"evidence_acceptance_state": "RAW_RESULT"}), "some_evidence_rejected"),
        (lambda e: e.update({"evidence_acceptance_state": "EVALUATED"}), "some_evidence_rejected"),
        (lambda e: e.update({"evidence_acceptance_state": "REJECTED"}), "some_evidence_rejected"),
        (lambda e: e.update({"evidence_acceptance_state": "INSUFFICIENT"}), "some_evidence_rejected"),
        (lambda e: e.update({"claim_id": "wrong_claim"}), "some_evidence_rejected"),
        (lambda e: e.update({"capability_id": "capability_wrong"}), "some_evidence_rejected"),
        (lambda e: e.pop("evidence_decision_id"), "some_evidence_rejected"),
        (lambda e: e.update({"source_provenance": {}}), "some_evidence_rejected"),
    ],
)
def test_unauthorized_evidence_inputs_fail_closed(mutation, reason):
    evidence = _accepted("accepted_a", causal=True)
    mutation(evidence)
    decision = _decision(CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED, [evidence])
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert reason in decision["promotion_failures"]


def test_missing_capability_id_fails_before_subject_creation():
    with pytest.raises(ValueError, match="capability_subject_requires_name_and_operation"):
        IntegratedCapabilityQualificationEngine().decide(
            {"capability_name": "", "operation": "replace_color"},
            [],
            requested_level=CapabilityQualificationLevel.ARCHITECTURALLY_PRESENT,
            architecture_present=True,
        )


def test_missing_qualification_decision_id_cannot_persist(tmp_path):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    decision = _decision(CapabilityQualificationLevel.ARCHITECTURALLY_PRESENT, [])
    decision.pop("qualification_decision_id")
    with pytest.raises(ValueError, match="qualification_decision_id_required"):
        engine.persist_decision(decision)


def test_same_source_repeated_across_runs_does_not_inflate_independence():
    evidence = [
        _accepted(f"accepted_{index}", source="source_a", run_id=f"run_{index}", causal=True)
        for index in range(10)
    ]
    decision = _decision(CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED, evidence)
    assert decision["independent_source_count"] == 1
    assert decision["decision_state"] == "PROMOTION_DENIED"


def test_same_source_repeated_across_tasks_does_not_inflate_independence():
    evidence = [
        _accepted(f"accepted_{index}", source="source_a", task_id=f"task_{index}", causal=True)
        for index in range(10)
    ]
    decision = _decision(CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED, evidence)
    assert decision["independent_source_count"] == 1
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert len(decision["origin_task_execution_ids"]) == 10
    assert decision["qualification_support_lineage_state"] == (
        "QUALIFICATION_SUPPORT_LINEAGE_COMPLETE"
    )


def test_multiple_artifact_ids_from_same_source_do_not_inflate_independence():
    evidence = [_accepted(f"accepted_{index}", source="source_a", causal=True) for index in range(10)]
    decision = _decision(CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED, evidence)
    assert decision["independent_source_count"] == 1
    assert decision["decision_state"] == "PROMOTION_DENIED"


def test_task_count_inflation_attack_fails_closed():
    evidence = _accepted("accepted_a", causal=True)
    evidence["distinct_task_count"] = 20
    decision = _decision(CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED, [evidence])
    assert decision["task_count_used_as_source_independence"] is False
    assert decision["decision_state"] == "PROMOTION_DENIED"


def test_run_count_inflation_attack_fails_closed():
    evidence = _accepted("accepted_a", causal=True)
    evidence["distinct_run_count"] = 20
    decision = _decision(CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED, [evidence])
    assert decision["run_count_used_as_source_independence"] is False
    assert decision["decision_state"] == "PROMOTION_DENIED"


def test_metric_threshold_direct_promotion_attack_fails_closed():
    evidence = _accepted("accepted_a")
    evidence["accuracy"] = 1.0
    decision = _decision(CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED, [evidence])
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert decision["raw_result_promotion_allowed"] is False


def test_historical_qualification_presented_as_current_does_not_grant_authority(tmp_path):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    stale = {
        "capability_id": capability_id_for_subject(_subject()),
        "current_qualification_level": "REPRODUCIBLY_SUPPORTED",
    }
    with pytest.raises(ValueError, match="qualification_decision_id_required"):
        engine.persist_decision(stale)


def test_persisted_state_without_authority_fails_closed(tmp_path):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    decision = _decision(CapabilityQualificationLevel.ARCHITECTURALLY_PRESENT, [])
    decision["qualification_authority"] = "NONE"
    with pytest.raises(ValueError, match="qualification_authority_required"):
        engine.persist_decision(decision)


def test_direct_highest_level_promotion_without_lower_requirements_fails_closed():
    decision = _decision(
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        [
            _accepted("accepted_a", source="source_a", causal=True),
            _accepted("accepted_b", source="source_b", causal=True),
        ],
        runtime_reachable=False,
    )
    assert decision["decision_state"] == "PROMOTION_DENIED"
    assert "runtime_reachability_not_established" in decision["promotion_failures"]


def test_direct_qualification_to_truth_transition_is_not_authorized():
    decision = _decision(
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        [
            _accepted("accepted_a", source="source_a", causal=True),
            _accepted("accepted_b", source="source_b", causal=True),
        ],
    )
    assert decision["qualification_implies_truth"] is False
    assert decision["authority"]["truth"] == "NONE"


def test_operational_observation_positive_case_stops_at_observed():
    decision = _decision(
        CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        [_accepted("accepted_a")],
    )
    assert decision["decision_state"] == "PROMOTION_GRANTED"
    assert decision["granted_level"] == "OPERATIONALLY_OBSERVED"


def test_causal_positive_case_stops_before_reproducible_support():
    decision = _decision(
        CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        [_accepted("accepted_a", causal=True)],
    )
    assert decision["decision_state"] == "PROMOTION_GRANTED"
    assert decision["granted_level"] == "CAUSALLY_DEMONSTRATED"
    reproducible = _decision(
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        [_accepted("accepted_a", causal=True)],
    )
    assert reproducible["decision_state"] == "PROMOTION_DENIED"


def test_persist_decision_records_current_state_with_no_external_authority(tmp_path):
    engine = IntegratedCapabilityQualificationEngine(tmp_path)
    result = engine.decide(
        _subject(),
        [_accepted("accepted_a", causal=True)],
        requested_level=CapabilityQualificationLevel.CAUSALLY_DEMONSTRATED,
        architecture_present=True,
        runtime_reachable=True,
    )
    persistence = engine.persist_decision(result["qualification_decision"])
    state = result["capability_qualification_state"]
    assert persistence["persistence_state"] == "PERSISTED_BY_QUALIFICATION_AUTHORITY"
    assert state["current_qualification_level"] == "CAUSALLY_DEMONSTRATED"
    assert state["truth_authority"] == "NONE"
    assert state["budget_authority"] == "NONE"


def test_accepted_evidence_copy_does_not_create_independence():
    evidence = _accepted("accepted_a", source="source_a", causal=True)
    copied = deepcopy(evidence)
    copied["accepted_evidence_id"] = "accepted_b"
    copied["claim_evidence_binding"]["accepted_evidence_id"] = "accepted_b"
    decision = _decision(
        CapabilityQualificationLevel.REPRODUCIBLY_SUPPORTED,
        [evidence, copied],
    )
    assert decision["independent_source_count"] == 1
    assert decision["decision_state"] == "PROMOTION_DENIED"


def test_capability_assessment_preserves_accepted_evidence_task_lineage():
    first = _accepted("accepted_a", source="source_a", task_id="task_a")
    second = _accepted("accepted_b", source="source_b", task_id="task_b")

    result = IntegratedCapabilityQualificationEngine().decide(
        _subject(),
        [first, second],
        requested_level=CapabilityQualificationLevel.OPERATIONALLY_OBSERVED,
        architecture_present=True,
        runtime_reachable=True,
    )
    assessment = result["capability_evidence_assessment"]
    decision = result["qualification_decision"]

    assert assessment["qualification_support_lineage_state"] == (
        "CAPABILITY_ASSESSMENT_LINEAGE_COMPLETE"
    )
    assert assessment["accepted_evidence_ids"] == [
        "accepted_a",
        "accepted_b",
    ]
    assert assessment["origin_task_execution_ids"] == [
        "task_execution_run_a_task_a",
        "task_execution_run_a_task_b",
    ]
    assert decision["qualification_support_lineage_state"] == (
        "QUALIFICATION_SUPPORT_LINEAGE_COMPLETE"
    )
    assert decision["qualification_support_attribution_semantics"] == (
        "DIRECT_SUPPORT_LINEAGE"
    )
    assert decision["task_provenance_authority"] == "NONE"
    assert decision["qualification_implies_truth"] is False
