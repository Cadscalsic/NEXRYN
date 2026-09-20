from pathlib import Path

import pytest

from runtime.experiments.adaptive_route_prediction_closure import (
    CONSUMED_VALIDATION_TASKS,
    run_closure_and_checkpoint,
)


@pytest.fixture(scope="module")
def closure_result(tmp_path_factory):
    root = tmp_path_factory.mktemp("adaptive_route_prediction_closure")
    return run_closure_and_checkpoint(
        program_artifact_dir=root / "program",
        checkpoint_root=root / "checkpoint",
    )


def test_candidate_v1_remains_immutable(closure_result):
    candidate = closure_result["closure"]["candidate_v1_state"]
    assert candidate["frozen_contract_preserved"] is True
    assert candidate["candidate_v1_mutated"] is False


def test_p2_remains_supported(closure_result):
    p2 = closure_result["closure"]["scientific_record"]["P2"]
    assert p2["status"] == "P2_ASSOCIATION_VALID"


def test_p3_v1_remains_failed(closure_result):
    p3 = closure_result["closure"]["scientific_record"]["P3_v1"]
    assert p3["status"] == "P3_PREDICTOR_FAILED"


def test_p4_remains_blocked(closure_result):
    assert closure_result["closure"]["p4_state"] == "BLOCKED"


def test_p5_remains_blocked(closure_result):
    assert closure_result["closure"]["p5_state"] == "BLOCKED"


def test_consumed_validation_set_is_preserved(closure_result):
    consumed = closure_result["closure"]["consumed_validation_evidence"]
    assert consumed["state"] == "CONSUMED_P3_V1_VALIDATION_EVIDENCE"
    assert consumed["task_ids"] == CONSUMED_VALIDATION_TASKS
    assert consumed["fresh_validation_for_candidate_v2"] is False


def test_closure_artifact_cannot_grant_authority(closure_result):
    authority = closure_result["closure"]["authority_state"]
    assert authority["adaptive_policy_patch_allowed"] is False
    assert authority["behavioral_authority"] == "NONE"


def test_closure_artifact_has_no_cognitive_consumer(closure_result):
    assert closure_result["closure"]["authority_state"]["cognitive_consumer_count"] == 0


def test_closure_cannot_alter_route_admission(closure_result):
    closure = closure_result["closure"]
    assert closure["future_hypothesis_state"]["not_policy_input"] is True
    assert closure["authority_state"]["production_behavior_changed"] == "NO"


def test_closure_cannot_alter_route_order(closure_result):
    assert closure_result["closure"]["authority_state"]["production_route_order_changed"] == "NO"


def test_closure_cannot_alter_route_budget(closure_result):
    assert closure_result["closure"]["authority_state"]["production_route_budget_changed"] == "NO"


def test_reopening_requires_new_information(closure_result):
    assert closure_result["closure"]["reopening_requirements"]["reopening_requires_new_information"] is True


def test_candidate_v2_is_not_created(closure_result):
    assert closure_result["closure"]["future_hypothesis_state"]["candidate_v2_created"] is False


def test_route_task_fit_remains_hypothesis_only(closure_result):
    hypothesis = closure_result["closure"]["future_hypothesis_state"]
    assert hypothesis["route_task_fit"] == "FUTURE_RESEARCH_HYPOTHESIS"
    assert hypothesis["not_runtime_variable"] is True


def test_production_behavior_unchanged(closure_result):
    assert closure_result["closure"]["authority_state"]["production_behavior_changed"] == "NO"


def test_closure_artifact_not_imported_by_runtime_paths():
    forbidden_paths = [
        Path("runtime/budget/runtime_budget_enforcer.py"),
        Path("runtime/planning"),
        Path("runtime/search"),
        Path("runtime/validation"),
        Path("runtime/truth"),
        Path("runtime/learning/training_assistant.py"),
    ]
    needle = "adaptive_route_prediction_closure"
    for path in forbidden_paths:
        if path.is_file():
            assert needle not in path.read_text(encoding="utf-8", errors="replace")
        elif path.is_dir():
            for file_path in path.rglob("*.py"):
                assert needle not in file_path.read_text(encoding="utf-8", errors="replace")


def test_next_gap_is_governed_evidence_acceptance(closure_result):
    next_gap = closure_result["next_gap_decision"]
    assert next_gap["selected_next_core_gap"] == "governed_evidence_acceptance_contract_completion"
    assert next_gap["classification"] == "CONFIRMED_ARCHITECTURAL_GAP"
    assert next_gap["selected_gap_required_action"] == "DESIGN_AND_REPAIR_BEFORE_STUDY"


def test_adaptive_route_prediction_v2_is_not_core_blocker(closure_result):
    gaps = closure_result["unresolved_gap_inventory"]["gaps"]
    adaptive = next(gap for gap in gaps if gap["gap_id"] == "adaptive_route_prediction_v2")
    assert adaptive["classification"] == "FUTURE_CAPABILITY_NOT_REQUIRED_FOR_CORE"
    assert adaptive["study_blocking"] == "NO"
