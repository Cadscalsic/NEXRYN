import json

import pytest

from runtime.learning.general_task_evidence_profile import (
    GeneralTaskEvidenceProfileError,
    ExpectedSourceDescriptorBuilder,
    GeneralTaskEvidenceProfiler,
    IndependentSourcePotentialEvaluator,
    MultiAxisEpistemicSelectionShadow,
    PreExecutionSourceDescriptorProviderDiscovery,
    TaskEvidenceMatcher,
)


def _write_task(path, payload):
    path.write_text(json.dumps(payload), encoding="utf-8")


def _elite_payload(task_id="elite_cognitive_task_12"):
    return {
        "train": [{"input": [[0]], "output": [[1]]}],
        "test": [{"input": [[0]]}],
        "expected_transformations": ["compose_capabilities"],
        "negative_controls": [{"reason": "simple_translation_is_insufficient"}],
        "nexryn_metadata": {
            "task_id": task_id,
            "curriculum": "nexryn_elite_training_curriculum_v1",
            "target_concepts": ["growth", "identity_preservation"],
            "target_domains": ["Identity", "Growth"],
            "required_operational_capabilities": [
                "candidate_generation",
                "world_model_validation",
            ],
            "independent_validation_opportunities": [
                "exact_validation",
                "independent_task_validation",
                "cross_domain_validation",
            ],
            "capability_graduation_targets": ["duplicate_object"],
            "governance_constraints": {
                "force_truth_promotion": False,
                "evidence_only": True,
            },
        },
    }


def test_profile_deterministically_binds_to_task_id(tmp_path):
    path = tmp_path / "elite_cognitive_task_12.json"
    _write_task(path, _elite_payload())
    profiler = GeneralTaskEvidenceProfiler()

    first = profiler.profile_task(path)
    second = profiler.profile_task(path)

    assert first["profile_id"] == second["profile_id"]
    assert first["task_id"] == "elite_cognitive_task_12"
    assert first["task_file"] == "elite_cognitive_task_12.json"


def test_profile_preserves_declared_and_derived_provenance(tmp_path):
    path = tmp_path / "elite_cognitive_task_12.json"
    _write_task(path, _elite_payload())

    profile = GeneralTaskEvidenceProfiler().profile_task(path)

    assert profile["profile_source"]["semantic_capabilities"] == "DECLARED_BY_TASK"
    assert profile["profile_source"]["evidence_types_potentially_supported"] == (
        "DERIVED_FROM_DECLARED_TASK_METADATA"
    )
    assert profile["known_baseline_sensitivity"] == "NEGATIVE_CONTROLS_DECLARED"
    assert profile["provenance"]["declared_metadata_only"] is True
    assert profile["pre_selection_observability"]["task_identity"] == "DECLARED"
    assert profile["pre_selection_observability"]["expected_source_lineage"] == (
        "UNKNOWN"
    )
    assert profile["expected_producer_component"] == (
        "VALIDATION_TASK_EXECUTION_PIPELINE"
    )
    descriptor = profile["expected_source_descriptor"]
    assert descriptor["producer_component"] == (
        "VALIDATION_TASK_EXECUTION_PIPELINE"
    )
    assert descriptor["derivation_basis"]["producer_component"] == (
        "VALIDATION_LANE_OWNED"
    )
    assert descriptor["derivation_basis"]["expected_source_lineage"] == "UNKNOWN"
    assert descriptor["grants_independence"] is False


def test_unknown_is_preserved_for_unlabeled_task(tmp_path):
    path = tmp_path / "task_001.json"
    _write_task(path, {"train": [{"input": [[0]], "output": [[0]]}]})

    profile = GeneralTaskEvidenceProfiler().profile_task(path)

    assert profile["semantic_capabilities"] == ["UNKNOWN"]
    assert profile["evidence_types_potentially_supported"] == ["UNKNOWN"]
    assert profile["profile_confidence"] == "UNKNOWN"


def test_profile_grants_no_selection_evidence_or_truth_authority(tmp_path):
    path = tmp_path / "elite_cognitive_task_12.json"
    _write_task(path, _elite_payload())

    profile = GeneralTaskEvidenceProfiler().profile_task(path)

    assert profile["authority"] == "OBSERVATION_ONLY"
    assert profile["behavioral_authority"] == "NONE"
    assert profile["evidence_acceptance_authority"] == "NONE"
    assert profile["selection_authority"] == "NONE"
    assert profile["truth_authority"] == "NONE"
    assert profile["trust_authority"] == "NONE"
    assert profile["graduation_authority"] == "NONE"
    assert profile["execution_authority"] == "NONE"


def test_task_12_profile_does_not_infer_high_value_from_success(tmp_path):
    path = tmp_path / "elite_cognitive_task_12.json"
    _write_task(path, _elite_payload())

    profile = GeneralTaskEvidenceProfiler().profile_task(
        path,
        selection_memory={
            "tasks": {
                "elite_cognitive_task_12.json": {
                    "times_selected": 4,
                    "last_run_id": "run_success",
                }
            }
        },
    )

    assert profile["prior_selection_count"] == 4
    assert profile["prior_execution_count"] == "UNKNOWN"
    assert profile["prior_evidence_contribution"] == "UNKNOWN"
    assert profile["profile_confidence"] == "MEDIUM"


def test_exact_required_evidence_match_succeeds(tmp_path):
    path = tmp_path / "elite_cognitive_task_12.json"
    _write_task(path, _elite_payload())
    profile = GeneralTaskEvidenceProfiler().profile_task(path)

    match = TaskEvidenceMatcher().match(
        {
            "requirement_id": "req_1",
            "evidence_type": "cross_source_consensus_evidence",
            "claim_domains": ["Identity"],
        },
        profile,
    )

    assert match["eligible"] is True
    assert match["match_strength"] == "EXACT_MATCH"
    assert match["selection_authority"] == "NONE"
    assert match["truth_authority"] == "NONE"


def test_incompatible_evidence_type_returns_no_match(tmp_path):
    path = tmp_path / "elite_cognitive_task_12.json"
    _write_task(path, _elite_payload())
    profile = GeneralTaskEvidenceProfiler().profile_task(path)

    match = TaskEvidenceMatcher().match(
        {
            "requirement_id": "req_1",
            "evidence_type": "replication_strength_evidence",
            "claim_domains": ["Color"],
        },
        profile,
    )

    assert match["eligible"] is False
    assert match["match_strength"] == "NO_MATCH"


def test_unknown_profile_cannot_become_strong_match(tmp_path):
    path = tmp_path / "task_001.json"
    _write_task(path, {"train": [{"input": [[0]], "output": [[0]]}]})
    profile = GeneralTaskEvidenceProfiler().profile_task(path)

    match = TaskEvidenceMatcher().match(
        {"requirement_id": "req_1", "evidence_type": "cross_source_consensus_evidence"},
        profile,
    )

    assert match["eligible"] is False
    assert match["match_strength"] == "UNKNOWN"


def test_missing_required_evidence_fails_closed(tmp_path):
    path = tmp_path / "elite_cognitive_task_20.json"
    _write_task(path, _elite_payload("elite_cognitive_task_20"))
    profile = GeneralTaskEvidenceProfiler().profile_task(path)

    with pytest.raises(GeneralTaskEvidenceProfileError):
        TaskEvidenceMatcher().match({}, profile)


def test_expected_source_descriptor_never_self_declares_independence():
    descriptor = ExpectedSourceDescriptorBuilder().build(
        {
            "source_lineage_targets": ["declared_lineage"],
        },
        evidence_types=["cross_source_consensus_evidence"],
        transformations=["replace_color"],
        validation_roles=["cross_domain_validation"],
    )

    assert descriptor["source_lineage_family"] == "declared_lineage"
    assert descriptor["derivation_basis"]["source_lineage_family"] == "TASK_OWNED"
    assert descriptor["task_identity_is_source_identity"] is False
    assert descriptor["expected_source_is_realized_source"] is False
    assert descriptor["grants_selection"] is False
    assert descriptor["grants_evidence"] is False
    assert descriptor["grants_truth"] is False
    assert descriptor["grants_independence"] is False
    assert descriptor["selection_authority"] == "NONE"


def test_independent_source_potential_distinguishes_unknown_and_represented(tmp_path):
    path = tmp_path / "elite_cognitive_task_12.json"
    payload = _elite_payload()
    payload["nexryn_metadata"]["source_lineage_targets"] = [
        "represented_lineage"
    ]
    _write_task(path, payload)
    profile = GeneralTaskEvidenceProfiler().profile_task(path)
    requirement = {
        "requirement_id": "req_1",
        "evidence_type": "cross_source_consensus_evidence",
        "claim_domains": ["Identity"],
    }
    match = TaskEvidenceMatcher().match(requirement, profile)
    potential = IndependentSourcePotentialEvaluator().evaluate(
        requirement,
        profile,
        match,
        {
            "source_relation_components": [{
                "members": [{
                    "lineage_roots": ["represented_lineage"],
                }],
            }],
        },
    )

    assert potential["potential_class"] == "ALREADY_REPRESENTED_SOURCE"
    assert potential["potential_is_proven_independence"] is False
    assert potential["selection_authority"] == "NONE"


def test_multi_axis_shadow_reports_policies_without_production_authority():
    rows = [
        {
            "task_file": "task_a.json",
            "base_score": 10.0,
            "base_rank": 1,
            "evidence_compatibility": 0.0,
            "independent_source_potential_score": 0.0,
        },
        {
            "task_file": "task_b.json",
            "base_score": 1.0,
            "base_rank": 2,
            "evidence_compatibility": 1.0,
            "independent_source_potential_score": 1.0,
        },
    ]

    matrix = MultiAxisEpistemicSelectionShadow().policy_matrix(
        rows,
        selected_count=1,
        base_selected_tasks=["task_a.json"],
    )

    assert matrix["production_selector_changed"] is False
    assert matrix["behavioral_integration_applied"] is False
    assert matrix["policies"]["production_baseline"]["selected_tasks"] == [
        "task_a.json"
    ]
    assert matrix["policies"]["evidence_compatibility_only"][
        "would_change_production_selection"
    ] is True


def test_provider_discovery_finds_partial_descriptor_provider_not_lineage_authority():
    report = PreExecutionSourceDescriptorProviderDiscovery().discover()

    assert report["legitimate_provider_found"] is True
    assert "ValidationLane" in report["legitimate_provider_ids"]
    assert report["legitimate_lineage_provider_found"] is False
    assert report["decision_gate"] == (
        "R2-C_LEGITIMATE_PROVIDER_EXISTS_WITH_USEFUL_COVERAGE_BUT_LOW_DISCRIMINATION"
    )
    assert report["route_is_source_lineage"] is False
    assert report["prediction_grants_epistemic_authority"] is False


def test_provider_discovery_rejects_historical_recurrence_as_independence():
    report = PreExecutionSourceDescriptorProviderDiscovery().discover()
    rows = {
        row["provider_id"]: row
        for row in report["provider_capability_matrix"]
    }

    historical = rows["ReusableLearnedObjectProvenance"]
    assert historical["descriptor_fields"]["expected_upstream_lineage"] == (
        "HISTORICALLY_INFERRED"
    )
    assert historical["legitimate_descriptor_provider"] is False
    assert historical["grants_independence"] is False
    assert historical["grants_truth"] is False
