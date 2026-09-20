from __future__ import annotations

from copy import deepcopy

from runtime.experiments.exact_subject_causal_replication import (
    exact_subject_credit_audit,
)
from runtime.epistemic.evidence_source_independence import (
    EvidenceSourceIndependenceEngine,
)


CONTRACT = {
    "capability_id": "capability_exact",
    "capability_operation": "replace_color",
    "qualification_claim_id": "claim_exact",
}


def _evidence(
    evidence_id: str,
    *,
    source: str,
    lineage: list[str],
    causal: bool = True,
    capability_id: str = "capability_exact",
    operation: str = "replace_color",
    claim_id: str = "claim_exact",
):
    state = "CAUSALLY_SUPPORTED" if causal else "CAUSAL_SUPPORT_NOT_ESTABLISHED"
    return {
        "accepted_evidence_id": evidence_id,
        "capability_id": capability_id,
        "capability_support_operation": operation,
        "target_operation": operation,
        "claim_id": claim_id,
        "canonical_source_identity": source,
        "source_lineage": lineage,
        "causal_support_state": state,
        "capability_causal_support_state": state,
        "causal_evidence": {
            "counterfactual_state": "COUNTERFACTUAL_VALID",
            "causal_effect": 1.0 if causal else 0.0,
        },
    }


def _audit(candidate):
    return exact_subject_credit_audit(
        contract=CONTRACT,
        baseline_evidence=_evidence(
            "baseline",
            source="source_a",
            lineage=["source_a", "context_a"],
        ),
        candidate_evidence=candidate,
    )


def test_valid_independent_causal_replication_counts_once():
    candidate = _evidence(
        "candidate",
        source="source_b",
        lineage=["source_b", "context_b"],
    )

    audit = _audit(candidate)

    assert audit["counts_as_independent_replication"] is True
    assert audit["source_relation_to_baseline"] == "INDEPENDENT"


def test_same_source_replay_does_not_count_despite_new_artifact_identity():
    candidate = _evidence(
        "candidate_new_id",
        source="source_a",
        lineage=["source_a", "different_context"],
    )

    audit = _audit(candidate)

    assert audit["counts_as_independent_replication"] is False
    assert audit["source_relation_to_baseline"] == "DEPENDENT"


def test_different_run_task_execution_ids_do_not_create_source_independence():
    candidate = _evidence(
        "candidate_new_id",
        source="source_a",
        lineage=["source_a"],
    )
    candidate.update({
        "run_id": "new_run",
        "task_id": "new_task",
        "execution_id": "new_execution",
        "schedule_id": "new_schedule",
        "origin_attempt_id": "new_attempt",
    })

    assert _audit(candidate)["counts_as_independent_replication"] is False


def test_independent_non_causal_source_gets_no_replication_credit():
    candidate = _evidence(
        "candidate",
        source="source_b",
        lineage=["source_b"],
        causal=False,
    )

    audit = _audit(candidate)

    assert audit["source_relation_to_baseline"] == "INDEPENDENT"
    assert audit["counts_as_independent_replication"] is False


def test_causal_dependent_source_gets_no_independent_replication_credit():
    candidate = _evidence(
        "candidate",
        source="source_b",
        lineage=["source_a", "derived_context"],
    )

    audit = _audit(candidate)

    assert audit["source_relation_to_baseline"] == "DEPENDENT"
    assert audit["counts_as_independent_replication"] is False


def test_wrong_capability_operation_or_claim_gets_no_credit():
    valid = _evidence("candidate", source="source_b", lineage=["source_b"])
    cases = [
        {**deepcopy(valid), "capability_id": "capability_other"},
        {**deepcopy(valid), "capability_support_operation": "rotate"},
        {**deepcopy(valid), "claim_id": "claim_other"},
    ]

    for candidate in cases:
        assert _audit(candidate)["counts_as_independent_replication"] is False


def test_target_capability_identity_is_not_source_lineage_by_itself():
    baseline = _evidence(
        "baseline",
        source="source_a",
        lineage=["source_a"],
    )
    candidate = _evidence(
        "candidate",
        source="source_b",
        lineage=["source_b"],
    )
    baseline["capability_id"] = "same_capability"
    candidate["capability_id"] = "same_capability"

    relation = EvidenceSourceIndependenceEngine().pairwise_independence(
        baseline,
        candidate,
    )

    assert relation["independence_state"] == "INDEPENDENT"
