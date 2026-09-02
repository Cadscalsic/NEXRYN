from runtime.epistemic import EvidenceSourceIndependenceEngine


def _evidence(
    evidence_id,
    *,
    claim_id="claim_a",
    run_id="run_a",
    task_id="task_a",
    producer_operation_id="producer_a",
    producer_component_id="component_a",
    producer_source_type="scheduled_validation_task",
    lineage=None,
):
    item = {
        "accepted_evidence_id": evidence_id,
        "claim_id": claim_id,
        "source_run_id": run_id,
        "selected_validation_task_id": task_id,
        "producer_operation_id": producer_operation_id,
        "producer_component_id": producer_component_id,
        "producer_source_type": producer_source_type,
        "required_evidence": "cross_source_consensus_evidence",
        "evidence_direction": "SUPPORTING",
        "acceptance_authority": "VALIDATION_EVIDENCE_EVALUATOR",
        "truth_authority": "NONE",
    }
    if lineage is not None:
        item["source_lineage"] = lineage
    return item


def test_same_evidence_artifact_twice_is_not_two_independent_sources():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence("accepted_a")
    second = _evidence("accepted_a", producer_operation_id="producer_b")

    relation = engine.pairwise_independence(first, second)

    assert relation["independence_state"] == "DEPENDENT"
    assert "SAME_EVIDENCE_ARTIFACT" in relation["reason"]


def test_same_canonical_source_under_different_evidence_ids_is_deduplicated():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence("accepted_a")
    second = _evidence("accepted_b")

    coverage = engine.source_coverage([first, second], claim_id="claim_a")

    assert coverage["supporting_evidence_count"] == 2
    assert coverage["current_proven_independent_source_count"] == 1


def test_different_run_alone_does_not_automatically_imply_independence():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence("accepted_a", run_id="run_a")
    second = _evidence("accepted_b", run_id="run_b")

    relation = engine.pairwise_independence(first, second)

    assert relation["independence_state"] == "DEPENDENT"
    assert "SAME_CANONICAL_SOURCE" in relation["reason"]


def test_different_task_alone_does_not_automatically_imply_independence():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence("accepted_a", task_id="task_a")
    second = _evidence("accepted_b", task_id="task_b")

    relation = engine.pairwise_independence(first, second)

    assert relation["independence_state"] == "DEPENDENT"
    assert "SAME_CANONICAL_SOURCE" in relation["reason"]


def test_different_producer_ids_with_shared_lineage_are_not_independent():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence(
        "accepted_a",
        producer_operation_id="producer_a",
        lineage=["shared_upstream"],
    )
    second = _evidence(
        "accepted_b",
        producer_operation_id="producer_b",
        lineage=["shared_upstream"],
    )

    relation = engine.pairwise_independence(first, second)

    assert relation["independence_state"] == "DEPENDENT"
    assert "SHARED_CAUSAL_ORIGIN" in relation["reason"]


def test_genuinely_distinct_source_identities_count_independently():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence(
        "accepted_a",
        producer_operation_id="producer_a",
        lineage=["upstream_a"],
    )
    second = _evidence(
        "accepted_b",
        producer_operation_id="producer_b",
        lineage=["upstream_b"],
    )

    coverage = engine.source_coverage([first, second], claim_id="claim_a")
    relation = engine.pairwise_independence(first, second)

    assert coverage["current_proven_independent_source_count"] == 2
    assert relation["independence_state"] == "INDEPENDENT"


def test_distinct_source_identities_with_shared_lineage_count_as_one_component():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence(
        "accepted_a",
        producer_operation_id="producer_a",
        lineage=["shared_upstream"],
    )
    second = _evidence(
        "accepted_b",
        producer_operation_id="producer_b",
        lineage=["shared_upstream"],
    )

    coverage = engine.source_coverage([first, second], claim_id="claim_a")

    assert len(coverage["source_identities"]) == 2
    assert coverage["current_proven_independent_source_count"] == 1
    assert coverage["dependent_supporting_sources"] == 1


def test_contradicting_independent_source_does_not_increase_support_count():
    engine = EvidenceSourceIndependenceEngine()
    supporting = _evidence(
        "accepted_support",
        producer_operation_id="producer_support",
        lineage=["support_lineage"],
    )
    contradicting = _evidence(
        "accepted_contra",
        producer_operation_id="producer_contra",
        lineage=["contra_lineage"],
    )
    contradicting["evidence_direction"] = "CONTRADICTING"

    coverage = engine.source_coverage([supporting, contradicting], claim_id="claim_a")

    assert coverage["proven_independent_supporting_sources"] == 1
    assert coverage["proven_independent_contradicting_sources"] == 1
    assert coverage["current_proven_independent_source_count"] == 1


def test_marginal_contribution_reports_plus_one_only_for_count_increase():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence(
        "accepted_a",
        producer_operation_id="producer_a",
        lineage=["lineage_a"],
    )
    second = _evidence(
        "accepted_b",
        producer_operation_id="producer_b",
        lineage=["lineage_b"],
    )
    before = engine.source_coverage([first], claim_id="claim_a")
    after = engine.source_coverage([first, second], claim_id="claim_a")

    contribution = engine.marginal_independent_contribution(
        before,
        after,
        "accepted_b",
    )

    assert contribution["contribution_state"] == (
        "+1_PROVEN_NEW_INDEPENDENT_SOURCE"
    )
    assert contribution["truth_authority"] == "NONE"


def test_marginal_contribution_zero_for_dependent_source():
    engine = EvidenceSourceIndependenceEngine()
    first = _evidence(
        "accepted_a",
        producer_operation_id="producer_a",
        lineage=["shared"],
    )
    second = _evidence(
        "accepted_b",
        producer_operation_id="producer_b",
        lineage=["shared"],
    )
    before = engine.source_coverage([first], claim_id="claim_a")
    after = engine.source_coverage([first, second], claim_id="claim_a")

    contribution = engine.marginal_independent_contribution(
        before,
        after,
        "accepted_b",
    )

    assert contribution["contribution_state"] == "0_ALREADY_REPRESENTED_SOURCE"


def test_missing_provenance_returns_unknown():
    engine = EvidenceSourceIndependenceEngine()
    evidence = {
        "accepted_evidence_id": "accepted_a",
        "claim_id": "claim_a",
        "evidence_direction": "SUPPORTING",
    }

    identity = engine.source_identity(evidence)
    coverage = engine.source_coverage([evidence], claim_id="claim_a")

    assert identity["source_identity_state"] == "UNKNOWN"
    assert coverage["current_proven_independent_source_count"] == 0


def test_potential_independence_does_not_certify_realized_independence():
    engine = EvidenceSourceIndependenceEngine()
    potential = engine.independent_source_potential(
        {
            "task_id": "task_candidate",
            "corpus_family": "elite",
            "evidence_types_potentially_supported": [
                "cross_source_consensus_evidence"
            ],
        },
        {"represented_source_families": []},
        {"evidence_type": "cross_source_consensus_evidence"},
    )

    assert potential["source_novelty_state"] == "POSSIBLY_NEW_SOURCE"
    assert potential["potential_independence_is_realized_independence"] is False
    assert potential["truth_authority"] == "NONE"


def test_realized_independence_does_not_grant_evidence_acceptance_or_truth():
    engine = EvidenceSourceIndependenceEngine()
    coverage = engine.source_coverage([
        _evidence("accepted_a", producer_operation_id="producer_a"),
        _evidence("accepted_b", producer_operation_id="producer_b"),
    ], claim_id="claim_a")

    assert coverage["evidence_acceptance_authority"] == "NONE"
    assert coverage["truth_authority"] == "NONE"


def test_independent_source_count_is_deterministic():
    engine = EvidenceSourceIndependenceEngine()
    evidence = [
        _evidence("accepted_b", producer_operation_id="producer_b"),
        _evidence("accepted_a", producer_operation_id="producer_a"),
    ]

    first = engine.source_coverage(evidence, claim_id="claim_a")
    second = engine.source_coverage(list(reversed(evidence)), claim_id="claim_a")

    assert first["source_identities"] == second["source_identities"]
    assert first["current_proven_independent_source_count"] == (
        second["current_proven_independent_source_count"]
    )


def test_historical_and_current_run_provenance_remain_distinct_fields():
    engine = EvidenceSourceIndependenceEngine()
    identity = engine.source_identity(
        _evidence("accepted_a", run_id="historical_run")
    )

    assert identity["source_identity_state"] == "PROVEN"
    assert "producer_operation_id" in identity["source_identity_payload"]
    assert "source_run_id" not in identity["source_identity_payload"]


def test_task_20_is_not_special_cased():
    engine = EvidenceSourceIndependenceEngine()
    identity = engine.source_identity(
        _evidence(
            "accepted_task20",
            task_id="elite_cognitive_task_20",
            producer_operation_id="producer_task20",
        )
    )

    assert identity["source_identity_state"] == "PROVEN"
    assert "elite_cognitive_task_20" not in identity["canonical_source_id"]


def test_task_12_is_not_special_cased():
    engine = EvidenceSourceIndependenceEngine()
    identity = engine.source_identity(
        _evidence(
            "accepted_task12",
            task_id="elite_cognitive_task_12",
            producer_operation_id="producer_task12",
        )
    )

    assert identity["source_identity_state"] == "PROVEN"
    assert "elite_cognitive_task_12" not in identity["canonical_source_id"]


def test_source_ontology_map_distinguishes_weak_and_canonical_fields():
    ontology = EvidenceSourceIndependenceEngine().source_ontology_map()
    by_field = {row["source_field"]: row for row in ontology}

    assert by_field["source_run_id"]["canonical"] is False
    assert by_field["source_task_id"]["canonical"] is False
    assert by_field["producer_operation_id"]["canonical"] is True


def test_pairwise_matrix_single_artifact_is_not_applicable():
    matrix = EvidenceSourceIndependenceEngine().pairwise_matrix([
        _evidence("accepted_a")
    ])

    assert matrix["state"] == "NOT_APPLICABLE_SINGLE_ARTIFACT"


def test_unknown_task_profile_potential_fails_closed():
    potential = EvidenceSourceIndependenceEngine().independent_source_potential(
        {"task_id": "task_unknown", "evidence_types_potentially_supported": ["UNKNOWN"]},
        {},
        {"evidence_type": "cross_source_consensus_evidence"},
    )

    assert potential["source_novelty_state"] == "UNKNOWN"
    assert potential["selection_authority"] == "NONE"
