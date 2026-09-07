from runtime.epistemic import (
    EpistemicSelectionCalibrationDatasetBuilder,
    EvidenceSourceIndependenceEngine,
    RealizedEpistemicContributionEngine,
)


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
        "evidence_acceptance_state": "ACCEPTED",
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


def test_realized_contribution_contract_is_observation_only():
    contract = RealizedEpistemicContributionEngine().contract()

    assert "canonical_source_identity" in contract["required_fields"]
    assert "marginal_independent_delta" in contract["required_fields"]
    assert contract["authority"] == "NONE"
    assert contract["grants_selection"] is False
    assert contract["grants_evidence"] is False
    assert contract["grants_truth"] is False
    assert contract["grants_independence"] is False


def test_real_r1_r2_shape_realizes_dependent_support_without_count_increase():
    engine = RealizedEpistemicContributionEngine()
    existing = _evidence(
        "accepted_r1",
        producer_operation_id="validation_execution_72adf97745e0",
        lineage=["r1_r2_shared_source"],
    )
    event = _evidence(
        "accepted_r2",
        run_id="run_r2",
        task_id="elite_cognitive_task_20",
        producer_operation_id="validation_execution_72adf97745e0",
        lineage=["r1_r2_shared_source"],
    )

    contribution = engine.assess_event(
        [existing],
        event,
        selection_context={
            "operational_rank_at_selection": 1,
            "evidence_compatibility_at_selection": 1.0,
            "expected_source_descriptor": {"source_lineage_family": "UNKNOWN"},
            "predicted_source_potential": "UNKNOWN",
        },
    )

    assert contribution["evidence_acceptance_state"] == "ACCEPTED"
    assert contribution["source_relation_to_existing_coverage"] == (
        "DEPENDENT_ON_EXISTING_COVERAGE"
    )
    assert contribution["independent_count_before"] == 1
    assert contribution["independent_count_after"] == 1
    assert contribution["marginal_independent_delta"] == 0
    assert contribution["contribution_class"] == "DEPENDENT_SUPPORT"
    assert contribution["selection_context_binding"]["realized_epistemic_delta"] == 0


def test_positive_control_distinct_canonical_lineage_increments_source_count():
    engine = RealizedEpistemicContributionEngine()
    existing = _evidence(
        "accepted_existing",
        producer_operation_id="producer_existing",
        lineage=["existing_lineage"],
    )
    distinct = _evidence(
        "accepted_distinct",
        producer_operation_id="producer_distinct",
        producer_component_id="component_distinct",
        lineage=["distinct_lineage"],
    )

    contribution = engine.assess_event([existing], distinct)

    assert contribution["independent_count_before"] == 1
    assert contribution["independent_count_after"] == 2
    assert contribution["marginal_independent_delta"] == 1
    assert contribution["contribution_class"] == "NEW_INDEPENDENT_SUPPORT"


def test_contradicting_independent_evidence_is_direction_aware():
    engine = RealizedEpistemicContributionEngine()
    supporting = _evidence(
        "accepted_support",
        producer_operation_id="producer_support",
        lineage=["support_lineage"],
    )
    contradicting = _evidence(
        "accepted_contradiction",
        producer_operation_id="producer_contradiction",
        producer_component_id="component_contradiction",
        lineage=["contradiction_lineage"],
    )
    contradicting["evidence_direction"] = "CONTRADICTING"

    contribution = engine.assess_event([supporting], contradicting)

    assert contribution["independent_count_before"] == 1
    assert contribution["independent_count_after"] == 1
    assert contribution["marginal_independent_delta"] == 0
    assert contribution["contradiction_delta"] == 1
    assert contribution["contribution_class"] == (
        "CONTRADICTORY_INDEPENDENT_EVIDENCE"
    )


def test_duplicate_and_dependent_attacks_produce_zero_marginal_delta():
    engine = RealizedEpistemicContributionEngine()
    baseline = _evidence(
        "accepted_base",
        producer_operation_id="producer_base",
        lineage=["shared_lineage"],
    )
    attacks = [
        _evidence(
            "accepted_base",
            producer_operation_id="producer_duplicate_id",
            lineage=["other_lineage"],
        ),
        _evidence(
            "accepted_same_source",
            run_id="run_other",
            task_id="task_other",
            producer_operation_id="producer_other",
            lineage=["shared_lineage"],
        ),
        _evidence(
            "accepted_same_canonical_source",
            run_id="run_other",
            task_id="task_other",
            producer_operation_id="producer_base",
            lineage=["other_lineage"],
        ),
    ]

    contributions = [
        engine.assess_event([baseline], attack)
        for attack in attacks
    ]

    assert [row["marginal_independent_delta"] for row in contributions] == [0, 0, 0]
    assert contributions[0]["contribution_class"] == "DUPLICATE_EVIDENCE"
    assert all(
        row["contribution_class"] in {"DUPLICATE_EVIDENCE", "DEPENDENT_SUPPORT"}
        for row in contributions
    )


def test_unknown_and_rejected_evidence_do_not_change_source_coverage():
    engine = RealizedEpistemicContributionEngine()
    baseline = _evidence(
        "accepted_base",
        producer_operation_id="producer_base",
        lineage=["base_lineage"],
    )
    unknown = {
        "accepted_evidence_id": "accepted_unknown",
        "claim_id": "claim_a",
        "source_run_id": "run_unknown",
        "selected_validation_task_id": "task_unknown",
        "evidence_direction": "SUPPORTING",
        "evidence_acceptance_state": "ACCEPTED",
    }
    rejected = _evidence(
        "accepted_rejected",
        producer_operation_id="producer_rejected",
        lineage=["rejected_lineage"],
    )
    rejected["evidence_acceptance_state"] = "REJECTED"

    unknown_contribution = engine.assess_event([baseline], unknown)
    rejected_contribution = engine.assess_event([baseline], rejected)

    assert unknown_contribution["contribution_class"] == "UNKNOWN_PROVENANCE"
    assert unknown_contribution["marginal_independent_delta"] == 0
    assert rejected_contribution["contribution_class"] == "REJECTED_EVIDENCE"
    assert rejected_contribution["independent_count_before"] == 1
    assert rejected_contribution["independent_count_after"] == 1


def test_prediction_vs_realization_and_quality_metrics_are_observational():
    engine = RealizedEpistemicContributionEngine()
    existing = _evidence(
        "accepted_existing",
        producer_operation_id="producer_existing",
        lineage=["existing_lineage"],
    )
    dependent = _evidence(
        "accepted_dependent",
        producer_operation_id="producer_existing",
        lineage=["other_lineage"],
    )
    novel = _evidence(
        "accepted_novel",
        producer_operation_id="producer_novel",
        producer_component_id="component_novel",
        lineage=["novel_lineage"],
    )

    report = engine.batch_report(
        [dependent, novel],
        initial_accepted_evidence=[existing],
        selection_context_by_evidence_id={
            "accepted_dependent": {
                "predicted_source_potential": "UNKNOWN",
                "operational_rank_at_selection": 3,
                "evidence_compatibility_at_selection": 0.82,
            },
            "accepted_novel": {
                "predicted_source_potential": "HIGH_POTENTIAL",
                "operational_rank_at_selection": 2,
                "evidence_compatibility_at_selection": 0.91,
            },
        },
    )

    classifications = [
        row["classification"]
        for row in report["prediction_vs_realization"]
    ]
    assert classifications == [
        "PREDICTED_UNKNOWN_REALIZED_DEPENDENT",
        "PREDICTED_NOVEL_REALIZED_NOVEL",
    ]
    assert report["quality_metrics"]["accepted_evidence_count"] == 2
    assert report["quality_metrics"]["independent_contribution_count"] == 1
    assert report["quality_metrics"]["dependent_support_count"] == 1
    assert report["quality_metrics"]["independent_yield"] == 0.5
    assert report["decision_gate"] == (
        "R4-D_REALIZED_CONTRIBUTION_OBSERVABLE_AND_SELECTION_CONTEXT_BOUND"
    )
    assert report["truth_authority"] == "NONE"


def test_calibration_observation_contract_has_no_authority():
    contract = EpistemicSelectionCalibrationDatasetBuilder().contract()

    assert "observation_id" in contract["required_fields"]
    assert "predicted_source_potential" in contract["pre_execution_fields"]
    assert "marginal_independent_delta" in contract["post_execution_fields"]
    assert contract["authority"] == "NONE"
    assert contract["selection_authority"] == "NONE"
    assert contract["truth_authority"] == "NONE"
    assert contract["budget_authority"] == "NONE"


def test_calibration_observation_identity_deduplicates_same_execution_event():
    contribution_engine = RealizedEpistemicContributionEngine()
    builder = EpistemicSelectionCalibrationDatasetBuilder()
    existing = _evidence(
        "accepted_existing",
        producer_operation_id="producer_existing",
        lineage=["shared"],
    )
    event = _evidence(
        "accepted_dependent",
        producer_operation_id="producer_other",
        lineage=["shared"],
    )
    contribution = contribution_engine.assess_event(
        [existing],
        event,
        selection_context={
            "operational_rank_at_selection": 1,
            "evidence_compatibility_at_selection": "STRONG_MATCH",
            "predicted_source_potential": "UNKNOWN",
        },
    )
    first = builder.observation(contribution)
    second = builder.observation(contribution)

    dataset = builder.dataset([first, second])

    assert first["observation_id"] == second["observation_id"]
    assert dataset["dataset_size"] == 1
    assert dataset["duplicate_observation_count"] == 1


def test_calibration_ready_observation_preserves_prediction_realization_boundary():
    contribution_engine = RealizedEpistemicContributionEngine()
    builder = EpistemicSelectionCalibrationDatasetBuilder()
    existing = _evidence(
        "accepted_existing",
        producer_operation_id="producer_existing",
        lineage=["shared"],
    )
    event = _evidence(
        "accepted_dependent",
        producer_operation_id="producer_other",
        lineage=["shared"],
    )
    contribution = contribution_engine.assess_event(
        [existing],
        event,
        selection_context={
            "operational_rank_at_selection": 3,
            "operational_score": 1026.7,
            "evidence_compatibility_at_selection": "STRONG_MATCH",
            "expected_source_descriptor": {"source_lineage_family": "UNKNOWN"},
            "predicted_source_potential": "UNKNOWN",
            "selection_reason": ["epistemic_shadow_signal_observed"],
            "repetition_count": 2,
        },
    )
    observation = builder.observation(contribution)

    assert observation["quality"]["observation_completeness"] == (
        "CALIBRATION_READY"
    )
    assert observation["quality"]["historical_policy_class"] == (
        "FULLY_PROVENANCE_NATIVE"
    )
    assert observation["pre_execution"]["predicted_source_potential"] == "UNKNOWN"
    assert observation["post_execution"]["realized_contribution_class"] == (
        "DEPENDENT_SUPPORT"
    )
    assert observation["authority"] == "NONE"


def test_partial_historical_observation_is_not_calibration_ready():
    builder = EpistemicSelectionCalibrationDatasetBuilder()
    contribution = {
        "claim_id": "claim_a",
        "task_id": "task_partial",
        "source_run_id": "run_partial",
        "accepted_evidence_id": "accepted_partial",
        "canonical_source_identity": "UNKNOWN",
        "source_relation_to_existing_coverage": "UNKNOWN_PROVENANCE",
        "contribution_class": "UNKNOWN_PROVENANCE",
        "independent_count_before": 1,
        "independent_count_after": 1,
        "marginal_independent_delta": 0,
        "contradiction_delta": 0,
        "evidence_acceptance_state": "ACCEPTED",
        "provenance_completeness": "PARTIAL",
    }

    observation = builder.observation(contribution)

    assert observation["quality"]["observation_completeness"] == "PARTIAL"
    assert observation["quality"]["historical_policy_class"] == "PARTIAL_HISTORICAL"


def test_pre_e1_unbound_observation_policy_is_preserved():
    builder = EpistemicSelectionCalibrationDatasetBuilder()
    contribution = {
        "claim_id": "claim_a",
        "task_id": "task_pre_e1",
        "source_run_id": "run_pre_e1",
        "accepted_evidence_id": "accepted_pre_e1",
        "canonical_source_identity": "UNKNOWN",
        "source_relation_to_existing_coverage": "UNKNOWN_PROVENANCE",
        "contribution_class": "UNKNOWN_PROVENANCE",
        "independent_count_before": 0,
        "independent_count_after": 0,
        "marginal_independent_delta": 0,
        "contradiction_delta": 0,
        "evidence_acceptance_state": "ACCEPTED",
        "provenance_completeness": "PARTIAL",
        "claim_evidence_binding_state": "PRE_E1_UNBOUND",
    }

    observation = builder.observation(contribution)

    assert observation["quality"]["historical_policy_class"] == "PRE_E1_UNBOUND"
    assert observation["quality"]["observation_completeness"] == "PARTIAL"


def test_calibration_dataset_reports_low_diversity_without_predictive_claim():
    contribution_engine = RealizedEpistemicContributionEngine()
    builder = EpistemicSelectionCalibrationDatasetBuilder()
    existing = _evidence(
        "accepted_existing",
        producer_operation_id="producer_existing",
        lineage=["shared"],
    )
    event = _evidence(
        "accepted_dependent",
        producer_operation_id="producer_other",
        lineage=["shared"],
    )
    contribution = contribution_engine.assess_event(
        [existing],
        event,
        selection_context={
            "operational_rank_at_selection": 1,
            "evidence_compatibility_at_selection": "EXACT_MATCH",
            "predicted_source_potential": "UNKNOWN",
            "repetition_count": 0,
        },
    )
    observation = builder.observation(contribution)

    dataset = builder.dataset([observation])

    assert dataset["calibration_ready_count"] == 1
    assert dataset["contribution_class_distribution"]["DEPENDENT_SUPPORT"] == 1
    assert dataset["prediction_vs_realization_matrix"]["UNKNOWN"][
        "DEPENDENT_SUPPORT"
    ] == 1
    assert dataset["evidence_compatibility_calibration"]["EXACT_MATCH"][
        "dependent_support_count"
    ] == 1
    assert dataset["repetition_value"]["FIRST_SELECTION"][
        "dependent_support_count"
    ] == 1
    assert dataset["data_sufficiency_level"] == "P0"
    assert dataset["decision_gate"] == (
        "R5-B_CALIBRATION_DATASET_EXISTS_BUT_LOW_DIVERSITY"
    )
    assert dataset["predictive_signal_status"] == (
        "INSUFFICIENT_FOR_PREDICTIVE_CLAIM"
    )
    assert dataset["selection_authority"] == "NONE"


def test_calibration_dataset_reaches_p1_only_after_five_ready_observations():
    contribution_engine = RealizedEpistemicContributionEngine()
    builder = EpistemicSelectionCalibrationDatasetBuilder()
    existing = _evidence(
        "accepted_existing",
        producer_operation_id="producer_existing",
        lineage=["shared"],
    )
    observations = []
    for index in range(5):
        event = _evidence(
            f"accepted_dependent_{index}",
            producer_operation_id=f"producer_dependent_{index}",
            lineage=["shared"],
        )
        contribution = contribution_engine.assess_event(
            [existing],
            event,
            selection_context={
                "operational_rank_at_selection": index + 1,
                "evidence_compatibility_at_selection": "STRONG_MATCH",
                "predicted_source_potential": "UNKNOWN",
            },
        )
        observations.append(builder.observation(contribution))

    dataset = builder.dataset(observations)

    assert dataset["dataset_size"] == 5
    assert dataset["calibration_ready_count"] == 5
    assert dataset["data_sufficiency_level"] == "P1"
    assert dataset["decision_gate"] == (
        "R5-B_CALIBRATION_DATASET_EXISTS_BUT_LOW_DIVERSITY"
    )
    assert dataset["calibration_metrics"]["conditional_probabilities"][
        "P_independent_given_predicted_source_potential"
    ] == "UNAVAILABLE"
