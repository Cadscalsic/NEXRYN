import json

import pytest

from runtime.learning.general_task_evidence_profile import (
    GeneralTaskEvidenceProfileError,
    GeneralTaskEvidenceProfiler,
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
