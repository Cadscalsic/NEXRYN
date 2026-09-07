import json

from core.world_model.counterfactual_simulator import CounterfactualSimulator
from core.world_model.position_predictor import PositionPredictor


def _run_counterfactual(profile_path=None):
    context = None
    if profile_path is not None:
        context = {
            "task_id": "b13_unit_task",
            "low_overhead_candidate_profiler_enabled": True,
            "candidate_cost_sample_interval": 4,
        }
    return CounterfactualSimulator(PositionPredictor()).simulate_position_counterfactuals(
        [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 0, 1], [0, 0, 0], [0, 0, 0]],
        operation="duplicate_object",
        position_rule={
            "operation": "duplicate_object",
            "source_object": "obj_1",
            "placement_vector": {"delta_row": 0, "delta_col": 1},
        },
        search_radius=1,
        runtime_context=context,
    )


def _semantic_projection(report):
    return {
        "candidate_count": report["candidate_count"],
        "candidate_vectors": [
            item["placement_vector"] for item in report["candidates"]
        ],
        "candidate_scores": [
            (item["accuracy"], item["difference_count"])
            for item in report["candidates"]
        ],
        "best_counterfactual": report["best_counterfactual"],
        "recommended_position_rule": report["recommended_position_rule"],
        "resolved": report["localized_prediction_mismatch_resolved"],
    }


def test_b13_low_overhead_profiler_preserves_counterfactual_semantics(
    tmp_path,
    monkeypatch,
):
    monkeypatch.delenv("NEXRYN_CANDIDATE_COST_PROFILE_PATH", raising=False)
    baseline = _run_counterfactual()

    profile_path = tmp_path / "candidate_profile.json"
    monkeypatch.setenv("NEXRYN_CANDIDATE_COST_PROFILE_PATH", str(profile_path))
    profiled = _run_counterfactual(profile_path)

    assert _semantic_projection(profiled) == _semantic_projection(baseline)
    assert profiled["low_overhead_candidate_cost_profile"]["authority"] == (
        "OBSERVATION_ONLY"
    )
    assert profiled["low_overhead_candidate_cost_profile"][
        "behavioral_authority"
    ] == "NONE"


def test_b13_low_overhead_profiler_records_minimum_aggregate_fields(
    tmp_path,
    monkeypatch,
):
    profile_path = tmp_path / "candidate_profile.json"
    monkeypatch.setenv("NEXRYN_CANDIDATE_COST_PROFILE_PATH", str(profile_path))

    report = _run_counterfactual(profile_path)
    profile = report["low_overhead_candidate_cost_profile"]

    assert profile["candidate_count"] == 9
    assert profile["candidates_started"] == 9
    assert profile["candidates_completed"] == 9
    assert profile["sampled_prediction_duration_ms"]
    assert profile["sampled_evaluation_duration_ms"]
    assert profile["aggregate_prediction_ms"] >= 0.0
    assert profile["aggregate_evaluation_ms"] >= 0.0
    assert profile["max_prediction_ms"] >= 0.0
    assert profile["max_evaluation_ms"] >= 0.0
    assert profile["source_node_count_distribution"]
    assert profile["target_node_count_distribution"]
    assert profile["match_attempt_distribution"]
    assert profile["candidate_index_at_timeout"] is None


def test_b13_low_overhead_profiler_flushes_one_compact_record(
    tmp_path,
    monkeypatch,
):
    profile_path = tmp_path / "candidate_profile.json"
    monkeypatch.setenv("NEXRYN_CANDIDATE_COST_PROFILE_PATH", str(profile_path))

    _run_counterfactual(profile_path)

    lines = profile_path.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 1
    profile = json.loads(lines[0])
    assert profile["system"] == "candidate_cost_profiler"
    assert "predicted_grid" not in lines[0]
    assert "expected_grid" not in lines[0]
