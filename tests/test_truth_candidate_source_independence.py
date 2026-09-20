from core.epistemic_models import Belief, BeliefState, EvidenceAggregate
from runtime.epistemic import EvidenceSourceIndependenceEngine
from runtime.truth_candidate_engine import TruthCandidateEngine


def _belief(concept="claim_a"):
    return Belief(
        concept=concept,
        claim=concept,
        state=BeliefState.VALIDATED,
        confidence=0.94,
    )


def _aggregate(concept="claim_a"):
    return EvidenceAggregate(
        concept=concept,
        evidence_strength=0.94,
        contradiction_score=0.02,
        semantic_consistency=0.94,
        causal_alignment=0.95,
    )


def _evidence(
    evidence_id,
    *,
    claim_id="claim_a",
    run_id="run_a",
    task_id="task_a",
    producer_operation_id="producer_a",
    lineage=None,
    direction="SUPPORTING",
):
    return {
        "accepted_evidence_id": evidence_id,
        "claim_id": claim_id,
        "source_run_id": run_id,
        "selected_validation_task_id": task_id,
        "producer_operation_id": producer_operation_id,
        "producer_component_id": "validation_pipeline",
        "producer_source_type": "scheduled_validation_task",
        "source_lineage": lineage or [producer_operation_id],
        "required_evidence": "cross_source_consensus_evidence",
        "evidence_direction": direction,
        "truth_authority": "NONE",
    }


def _coverage(evidence):
    return EvidenceSourceIndependenceEngine().source_coverage(
        evidence,
        claim_id="claim_a",
        required_independent_sources=(
            TruthCandidateEngine.MINIMUM_INDEPENDENT_SOURCES
        ),
    )


def _evaluate(evidence, *, used_task_count=0):
    return TruthCandidateEngine().evaluate(
        _belief(),
        _aggregate(),
        {
            "knowledge_generalization": {
                "used_task_count": used_task_count,
            },
            "source_coverage": _coverage(evidence),
        },
    )


def test_canonical_source_count_field_reaches_truth_candidate_engine():
    evidence = [
        _evidence(f"accepted_{index}", producer_operation_id=f"producer_{index}")
        for index in range(8)
    ]

    report = _evaluate(evidence, used_task_count=1)

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 8
    assert report["independent_source_requirement_satisfied"] is True
    assert report["legacy_independent_task_coverage"] == 1
    assert report["legacy_independent_task_metric_policy"] == "DIAGNOSTIC_ONLY"


def test_truth_engine_does_not_recompute_independence_from_task_ids():
    evidence = [
        _evidence(
            f"accepted_{index}",
            task_id=f"task_{index}",
            producer_operation_id="same_producer",
            lineage=["same_source"],
        )
        for index in range(8)
    ]

    report = _evaluate(evidence, used_task_count=8)

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 1
    assert report["eligible_for_truth_candidate"] is False
    assert "independent_task_coverage" not in report["blocked_metrics"]
    assert report["truth_independence_evidence"][
        "task_diversity_grants_independence"
    ] is False


def test_eight_distinct_task_ids_same_source_lineage_count_as_one():
    evidence = [
        _evidence(
            f"accepted_{index}",
            task_id=f"task_{index}",
            producer_operation_id="same_producer",
            lineage=["same_lineage"],
        )
        for index in range(8)
    ]

    report = _evaluate(evidence, used_task_count=8)

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 1
    assert report["independent_source_requirement_satisfied"] is False


def test_eight_distinct_run_ids_same_source_lineage_count_as_one():
    evidence = [
        _evidence(
            f"accepted_{index}",
            run_id=f"run_{index}",
            producer_operation_id="same_producer",
            lineage=["same_lineage"],
        )
        for index in range(8)
    ]

    report = _evaluate(evidence)

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 1
    assert report["eligible_for_truth_candidate"] is False


def test_eight_distinct_evidence_ids_same_source_count_as_one():
    evidence = [
        _evidence(
            f"accepted_{index}",
            producer_operation_id="same_producer",
            lineage=["same_lineage"],
        )
        for index in range(8)
    ]

    report = _evaluate(evidence)

    assert report["truth_independence_evidence"][
        "accepted_evidence_count"
    ] == 8
    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 1
    assert report["eligible_for_truth_candidate"] is False


def test_shared_dependence_lineage_does_not_inflate_distinct_source_ids():
    evidence = [
        _evidence(
            f"accepted_{index}",
            producer_operation_id=f"producer_{index}",
            lineage=["shared_upstream"],
        )
        for index in range(8)
    ]

    report = _evaluate(evidence)

    assert len(report["source_coverage"]["source_identities"]) == 8
    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 1
    assert report["eligible_for_truth_candidate"] is False


def test_eight_proven_independent_supporting_sources_satisfy_gate_only():
    evidence = [
        _evidence(
            f"accepted_{index}",
            producer_operation_id=f"producer_{index}",
            lineage=[f"lineage_{index}"],
        )
        for index in range(8)
    ]

    report = _evaluate(evidence)

    assert report["independent_source_requirement_satisfied"] is True
    assert report["eligible_for_truth_candidate"] is True
    assert report["automatic_truth_commit_forbidden"] is True


def test_seven_proven_independent_sources_do_not_satisfy_gate():
    evidence = [
        _evidence(
            f"accepted_{index}",
            producer_operation_id=f"producer_{index}",
            lineage=[f"lineage_{index}"],
        )
        for index in range(7)
    ]

    report = _evaluate(evidence)

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 7
    assert report["remaining_independent_source_deficit"] == 1
    assert report["eligible_for_truth_candidate"] is False


def test_unknown_provenance_does_not_count_toward_truth_gate():
    proven = [
        _evidence(
            f"accepted_{index}",
            producer_operation_id=f"producer_{index}",
            lineage=[f"lineage_{index}"],
        )
        for index in range(7)
    ]
    unknown = [
        {
            "accepted_evidence_id": f"unknown_{index}",
            "claim_id": "claim_a",
            "evidence_direction": "SUPPORTING",
        }
        for index in range(20)
    ]

    report = _evaluate(proven + unknown)

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 7
    assert report["truth_independence_evidence"][
        "unknown_source_relation_count"
    ] == 20
    assert report["eligible_for_truth_candidate"] is False


def test_dependent_repetition_does_not_count_toward_truth_gate():
    first = _evidence("accepted_a", producer_operation_id="producer_a")
    repeat = _evidence("accepted_b", producer_operation_id="producer_a")

    report = _evaluate([first, repeat])

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 1
    assert report["truth_independence_evidence"]["dependent_source_count"] == 1
    assert report["eligible_for_truth_candidate"] is False


def test_contradicting_independent_sources_do_not_satisfy_supporting_gate():
    supporting = [
        _evidence(
            f"support_{index}",
            producer_operation_id=f"support_producer_{index}",
            lineage=[f"support_lineage_{index}"],
        )
        for index in range(5)
    ]
    contradicting = [
        _evidence(
            f"contra_{index}",
            producer_operation_id=f"contra_producer_{index}",
            lineage=[f"contra_lineage_{index}"],
            direction="CONTRADICTING",
        )
        for index in range(3)
    ]

    report = _evaluate(supporting + contradicting)

    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 5
    assert report["truth_independence_evidence"][
        "proven_independent_contradicting_source_count"
    ] == 3
    assert report["eligible_for_truth_candidate"] is False


def test_source_coverage_absent_fails_closed_without_task_count_fallback():
    report = TruthCandidateEngine().evaluate(
        _belief(),
        _aggregate(),
        {
            "knowledge_generalization": {
                "used_task_count": 8,
            },
        },
    )

    assert report["truth_independence_evidence"][
        "source_coverage_available"
    ] is False
    assert report["truth_independence_evidence"][
        "proven_independent_supporting_source_count"
    ] == 0
    assert report["eligible_for_truth_candidate"] is False
    assert "independent_task_coverage" not in report["blocked_metrics"]
    assert "proven_independent_supporting_source_count" in report["blocked_metrics"]


def test_claim_mismatch_source_coverage_fails_closed():
    coverage = _coverage([
        _evidence(
            f"accepted_{index}",
            producer_operation_id=f"producer_{index}",
            lineage=[f"lineage_{index}"],
        )
        for index in range(8)
    ])
    coverage["claim_id"] = "other_claim"

    report = TruthCandidateEngine().evaluate(
        _belief("claim_a"),
        _aggregate("claim_a"),
        {"source_coverage": coverage},
    )

    assert report["truth_independence_evidence"]["claim_id"] == "other_claim"
    assert report["truth_independence_evidence"][
        "source_coverage_claim_matches_truth_claim"
    ] is False
    assert report["eligible_for_truth_candidate"] is False
    assert report["truth_independence_evidence"]["authority"] == (
        "EPISTEMIC_OBSERVATION"
    )
