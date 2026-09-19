from copy import deepcopy

import pytest

from runtime.arena import (
    CandidateProposalGateway,
    CandidateSimulator,
    CandidateScorer,
    CandidateSupportGroundingEngine,
    CognitiveCandidateArena,
    apply_candidate_support_grounding,
)


def _candidate(**overrides):
    value = {
        "candidate_id": "candidate-a",
        "operation": "replace_color",
        "run_id": "run-current",
        "task_id": "task-current",
        "execution_plan_id": "plan-current",
        "program": {"steps": [{"operation": "replace_color", "parameters": {}}]},
    }
    value.update(overrides)
    return value


def _evidence(**overrides):
    value = {
        "accepted_evidence_id": "accepted-1",
        "evidence_acceptance_state": "ACCEPTED",
        "candidate_id": "candidate-a",
        "run_id": "run-current",
        "independence_state": "INDEPENDENT",
        "provenance_verified": True,
        "immutable_fingerprint": "evidence-fingerprint",
        "support_value": 0.8,
        "contradiction": False,
    }
    value.update(overrides)
    return value


def _localization(**overrides):
    value = {
        "observation_id": "localization-1",
        "candidate_id": "candidate-a",
        "run_id": "run-current",
        "independence_state": "INDEPENDENT",
        "provenance_verified": True,
        "immutable_fingerprint": "localization-fingerprint",
        "predicted_affected_cells": [[0, 0], [0, 1]],
        "observed_affected_cells": [[0, 0], [0, 1]],
    }
    value.update(overrides)
    return value


def test_explicit_accepted_truth_support_is_evidence_derived():
    result = CandidateSupportGroundingEngine().ground(
        _candidate(truth_support_observations=[_evidence()])
    )["truth_support_metric"]
    assert result["normalized_value"] == 0.8
    assert result["value_origin"] == "EVIDENCE_DERIVED"
    assert result["evidence_references"] == ["accepted-1"]


def test_missing_truth_input_has_distinguishable_neutral_origin():
    result = CandidateSupportGroundingEngine().ground(_candidate())["truth_support_metric"]
    assert result["normalized_value"] == 0.5
    assert result["value_origin"] == "INSUFFICIENT_EVIDENCE"
    assert result["missing_data_reason"]


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"evidence_acceptance_state": "REJECTED"}, "EVIDENCE_NOT_ACCEPTED"),
        ({"evidence_type": "D8_DIRECTIONAL"}, "D8_DIRECTION_IS_NOT_ACCEPTED_EVIDENCE"),
        ({"independence_state": "SELF_GENERATED"}, "SOURCE_NOT_INDEPENDENT"),
        ({"candidate_id": "candidate-b"}, "CANDIDATE_IDENTITY_MISMATCH"),
        ({"run_id": "run-foreign"}, "SOURCE_RUN_MISMATCH"),
        ({"provenance_verified": False}, "PROVENANCE_NOT_VERIFIED"),
        ({"contradiction": True}, "CONTRADICTORY_EVIDENCE"),
        ({"support_value": None}, "MISSING_SUPPORT_VALUE"),
    ],
)
def test_unlawful_truth_inputs_fail_closed(override, reason):
    result = CandidateSupportGroundingEngine().ground(
        _candidate(truth_support_observations=[_evidence(**override)])
    )["truth_support_metric"]
    assert result["value_origin"] == "INSUFFICIENT_EVIDENCE"
    assert result["rejected_inputs"][0]["reason"] == reason


def test_duplicate_truth_evidence_is_not_double_counted():
    result = CandidateSupportGroundingEngine().ground(
        _candidate(truth_support_observations=[_evidence(), _evidence(support_value=1.0)])
    )["truth_support_metric"]
    assert result["normalized_value"] == 0.8
    assert result["duplicate_count"] == 1


@pytest.mark.parametrize(
    ("observed", "expected"),
    [
        ([[0, 0], [0, 1]], 1.0),
        ([[0, 0]], 0.5),
        ([[1, 0]], 0.0),
    ],
)
def test_localization_quality_is_mask_jaccard(observed, expected):
    result = CandidateSupportGroundingEngine().ground(
        _candidate(localization_observations=[_localization(observed_affected_cells=observed)])
    )["localization_quality_metric"]
    assert result["normalized_value"] == expected
    assert result["value_origin"] == "MEASURED"


def test_non_spatial_operation_is_not_applicable():
    result = CandidateSupportGroundingEngine().ground(
        _candidate(operation="classify")
    )["localization_quality_metric"]
    assert result["value_origin"] == "NOT_APPLICABLE"


def test_missing_localization_is_explicitly_insufficient():
    result = CandidateSupportGroundingEngine().ground(_candidate())["localization_quality_metric"]
    assert result["normalized_value"] == 0.5
    assert result["value_origin"] == "INSUFFICIENT_EVIDENCE"


@pytest.mark.parametrize(
    ("override", "reason"),
    [
        ({"candidate_id": "candidate-b"}, "CANDIDATE_IDENTITY_MISMATCH"),
        ({"run_id": "run-foreign"}, "SOURCE_RUN_MISMATCH"),
        ({"provenance_verified": False}, "PROVENANCE_NOT_VERIFIED"),
        ({"independence_state": "SELF_GENERATED"}, "OBSERVATION_NOT_INDEPENDENT"),
        ({"observed_affected_cells": None}, "LOCALIZATION_MASK_MISSING"),
    ],
)
def test_unlawful_localization_inputs_fail_closed(override, reason):
    result = CandidateSupportGroundingEngine().ground(
        _candidate(localization_observations=[_localization(**override)])
    )["localization_quality_metric"]
    assert result["value_origin"] == "INSUFFICIENT_EVIDENCE"
    assert result["rejected_inputs"][0]["reason"] == reason


def test_metric_recomputation_is_deterministic_except_identity_timestamp():
    engine = CandidateSupportGroundingEngine()
    first = engine.ground(_candidate(truth_support_observations=[_evidence()]))
    second = engine.ground(_candidate(truth_support_observations=[_evidence()]))
    assert first["truth_support_metric"]["normalized_value"] == second["truth_support_metric"]["normalized_value"]
    assert first["truth_support_metric"]["evidence_references"] == second["truth_support_metric"]["evidence_references"]


def test_candidate_scorer_consumes_grounded_values_and_preserves_origins():
    candidate = _candidate(
        truth_support_observations=[_evidence()],
        localization_observations=[_localization()],
        target_size=1,
    )
    grounding = CandidateSupportGroundingEngine().ground(candidate)
    candidate["truth_support_metric"] = grounding["truth_support_metric"]
    candidate["localization_quality_metric"] = grounding["localization_quality_metric"]
    candidate["truth_support"] = grounding["truth_support_metric"]["normalized_value"]
    candidate["localization_support"] = grounding["localization_quality_metric"]["normalized_value"]
    score = CandidateScorer().score(candidate, {"prediction_accuracy": 1.0})
    assert score["score_components"]["truth_support"] == 0.8
    assert score["score_components"]["localization_quality"] == 1.0
    assert score["score_composition"]["raw_inputs"]["truth_support_metric"]["value_origin"] == "EVIDENCE_DERIVED"
    assert score["score_composition"]["authority"] == "OBSERVATION_ONLY"
    assert score["score_composition"]["behavioral_authority"] == "NONE"


def test_altered_localization_mask_changes_fingerprint_and_value():
    engine = CandidateSupportGroundingEngine()
    first = engine.ground(_candidate(localization_observations=[_localization()]))
    second = engine.ground(_candidate(localization_observations=[_localization(observed_affected_cells=[[1, 1]])]))
    assert first["localization_quality_metric"]["immutable_fingerprint"] != second["localization_quality_metric"]["immutable_fingerprint"]
    assert first["localization_quality_metric"]["normalized_value"] != second["localization_quality_metric"]["normalized_value"]


def test_metric_records_never_grant_behavioral_authority():
    result = CandidateSupportGroundingEngine().ground(
        _candidate(truth_support_observations=[_evidence()], localization_observations=[_localization()])
    )
    for metric in (result["truth_support_metric"], result["localization_quality_metric"]):
        assert metric["authority"] == "OBSERVATION_ONLY"
        assert metric["behavioral_authority"] == "NONE"


def test_proposal_adapter_propagates_explicit_missing_origins():
    proposal = apply_candidate_support_grounding(
        {
            "candidate_id": "candidate-adapter",
            "source": "semantic_compiler",
            "operation": "replace_color",
            "program": {
                "steps": [{"operation": "replace_color", "parameters": {}}]
            },
        }
    )
    assert proposal["truth_support"] == 0.5
    assert proposal["truth_support_metric"]["value_origin"] == "INSUFFICIENT_EVIDENCE"
    assert proposal["localization_support"] == 0.5
    assert proposal["localization_quality_metric"]["value_origin"] == "INSUFFICIENT_EVIDENCE"
    assert proposal["candidate_support_grounding"]["behavioral_authority"] == "NONE"

    gateway = CandidateProposalGateway().submit([proposal])["proposals"][0]
    assert gateway["truth_support_metric"]["value_origin"] == "INSUFFICIENT_EVIDENCE"
    assert gateway["localization_quality_metric"]["value_origin"] == "INSUFFICIENT_EVIDENCE"
    assert gateway["candidate_support_grounding"]["behavioral_authority"] == "NONE"


def test_arena_rebinds_support_metrics_to_canonical_candidate_and_current_run():
    report = CognitiveCandidateArena().run(
        [{
            "candidate_id": "candidate:canonical",
            "source": "semantic_compiler",
            "operation": "replace_color",
            "program": {"steps": [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}}}]},
            "source_confidence": 0.8,
        }],
        input_grid=[[1]],
        target_grid=[[2]],
        runtime_context={
            "run_id": "run-canonical",
            "task_id": "task-canonical",
            "execution_plan_id": "plan-canonical",
        },
        analysis_only=True,
    )
    candidate = report["normalized_candidates"][0]
    metric = candidate["truth_support_metric"]
    assert metric["candidate_id"] == candidate["candidate_id"]
    assert metric["run_id"] == "run-canonical"
    assert metric["task_id"] == "task-canonical"
    assert metric["execution_plan_id"] == "plan-canonical"


@pytest.mark.parametrize(
    ("predicted", "target", "expected"),
    [
        ([[0, 0], [0, 1]], [[2, 2]], 1.0),
        ([[0, 0], [0, 1]], [[2, 1]], 0.5),
        ([[0, 0]], [[2, 2]], 0.5),
        ([[0, 0], [0, 1]], [[1, 2]], 0.5),
    ],
)
def test_simulator_produces_predeclared_then_observed_localization(predicted, target, expected):
    candidate = _candidate(
        program={"steps": [{
            "operation": "replace_color",
            "parameters": {"color_mapping": {1: 2}, "affected_positions": predicted},
        }]},
    )
    simulation = CandidateSimulator().simulate(candidate, input_grid=[[1, 1]], target_grid=target)
    observation = simulation["localization_observation"]
    assert observation["prediction_timestamp"] <= observation["observation_timestamp"]
    assert observation["predicted_affected_cells"] == predicted
    candidate["localization_observations"] = [observation]
    result = CandidateSupportGroundingEngine().ground(candidate)["localization_quality_metric"]
    assert result["normalized_value"] == expected
    assert observation["authority"] == "OBSERVATION_ONLY"
    assert observation["behavioral_authority"] == "NONE"


def test_simulator_localization_preserved_regions_are_explicit():
    simulation = CandidateSimulator().simulate(
        _candidate(program={"steps": [{"operation": "replace_color", "parameters": {"color_mapping": {1: 2}, "affected_positions": [[0, 0]]}}]}),
        input_grid=[[1, 1]], target_grid=[[2, 1]],
    )
    observation = simulation["localization_observation"]
    assert observation["predicted_preserved_cells"] == [[0, 1]]
    assert observation["observed_preserved_cells"] == [[0, 1]]
    assert observation["false_positive_cells"] == []
    assert observation["missed_cells"] == []


def test_simulator_rejects_unavailable_localization_ground_truth():
    simulation = CandidateSimulator().simulate(
        _candidate(), input_grid=[[1]], target_grid=None,
    )
    assert simulation["localization_observation"]["applicability_state"] == "OBSERVATION_UNAVAILABLE"
