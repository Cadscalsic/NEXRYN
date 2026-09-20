from pathlib import Path

from runtime.experiments.c5_target_set_prequalification import (
    classify_candidate,
    context_readiness,
    freeze_readiness_gate,
    run_prequalification,
)


def _subject(index: int, *, contexts=2, sources=2, c4=True, operation=None):
    operation = operation or f"operation_{index}"
    return {
        "capability_id": f"capability_{index}",
        "capability_subject": {
            "capability_name": f"capability_{index}",
            "operation": operation,
            "domain": "fixture",
            "qualifiers": {"validation_context": f"context_{index}_a"},
        },
        "operation": operation,
        "qualification_claim_id": f"claim_{index}",
        "current_qualification_level": (
            "REPRODUCIBLY_SUPPORTED" if c4 else "CAUSALLY_DEMONSTRATED"
        ),
        "C4_state": "C4_PASSED" if c4 else "C4_NOT_PASSED_INSUFFICIENT_SOURCES",
        "accepted_causal_evidence_count": sources,
        "independent_causal_source_count": sources,
        "canonical_source_ids": [
            f"source_{index}_{offset}" for offset in range(max(sources, 0))
        ],
        "contexts": [f"context_{index}_{offset}" for offset in range(contexts)],
        "context_count": contexts,
        "counterfactual_method": "CONTROLLED_TRANSFORMATION_EFFECT",
        "causal_estimand": "treatment_score - control_score",
        "accepted_evidence_ids": [f"accepted_{index}_{offset}" for offset in range(sources)],
    }


def test_candidate_classification_preserves_exact_subject_identity():
    subject = _subject(1)

    result = classify_candidate(subject)

    assert result["prequalification_state"] == "C5_ELIGIBLE_NOW"
    assert result["capability_id"] == "capability_1"
    assert result["operation"] == "operation_1"
    assert result["qualification_claim_id"] == "claim_1"


def test_not_ready_when_same_context_is_replayed_without_context_diversity():
    subject = _subject(1, contexts=1, sources=2)
    subject["task_count"] = 2

    result = classify_candidate(subject)

    assert result["prequalification_state"] == "C5_NOT_READY"
    assert "second_exact_subject_context_not_demonstrated" in result["missing_requirements"]
    assert result["context_readiness"]["context_diversity_type"] == "SAME_CONTEXT_REPLAY"


def test_prequalified_requires_reachable_second_context_not_c4_success():
    subject = _subject(1, contexts=1, sources=1, c4=False)
    subject["future_reachable_contexts"] = ["context_1_b"]

    result = classify_candidate(subject)

    assert result["prequalification_state"] == "C5_PREQUALIFIED_CANDIDATE"
    assert result["reachable_context_count"] == 2


def test_freeze_gate_rejects_insufficient_capability_and_operation_diversity():
    candidates = [
        classify_candidate(_subject(1, operation="same_operation")),
        classify_candidate(_subject(2, operation="same_operation")),
        classify_candidate(_subject(3, operation="same_operation")),
    ]

    result = freeze_readiness_gate(candidates)

    assert result["primary_freeze_readiness_decision"] == "NOT_READY_TO_FREEZE_C5_TARGET_SET"
    assert "fewer_than_two_operations" in result["failure_reasons"]


def test_freeze_gate_ready_with_three_capabilities_two_operations_and_sources():
    candidates = [
        classify_candidate(_subject(1, operation="operation_a")),
        classify_candidate(_subject(2, operation="operation_b")),
        classify_candidate(_subject(3, operation="operation_b")),
    ]

    result = freeze_readiness_gate(candidates)

    assert result["primary_freeze_readiness_decision"] == "READY_TO_FREEZE_C5_TARGET_SET"
    assert result["provisional_target_set_size"] == 3
    assert result["unique_capability_count"] == 3
    assert result["unique_operation_count"] == 2


def test_context_readiness_does_not_count_same_operation_context_as_exact_subject_context():
    subject = _subject(1, contexts=1)

    result = context_readiness(
        subject,
        known_operation_contexts={"operation_1": ["context_1_0", "context_elsewhere"]},
    )

    assert result["reachable_context_count"] == 1
    assert result["same_operation_contexts_not_counted_for_exact_subject"] == [
        "context_elsewhere"
    ]


def test_run_prequalification_writes_only_requested_artifact_tree(tmp_path: Path):
    result = run_prequalification(output_root=tmp_path)

    output_dir = Path(result["output_dir"])
    assert output_dir.is_relative_to(tmp_path)
    assert (output_dir / "summary.json").exists()
    assert (output_dir / "c5_candidate_readiness_matrix.json").exists()
    assert not (output_dir / "c5_provisional_target_set.json").exists()
    assert result["c5_target_set_frozen"] is False
    assert result["c5_campaign_executed"] is False
