import json

from core.world_model.counterfactual_simulator import CounterfactualSimulator
from core.world_model.position_predictor import PositionPredictor


class CountingObjectExtractor:
    def __init__(self):
        self.normalize_calls = 0
        self.extract_calls = 0

    def normalize_grid(self, grid):
        self.normalize_calls += 1
        return [list(row) for row in grid]

    def extract_objects(self, grid):
        self.extract_calls += 1
        normalized = self.normalize_grid(grid)
        cells = [
            [row_index, col_index]
            for row_index, row in enumerate(normalized)
            for col_index, value in enumerate(row)
            if value != 0
        ]
        if not cells:
            return []
        return [
            {
                "id": "obj_1",
                "color": normalized[cells[0][0]][cells[0][1]],
                "cells": cells,
                "size": len(cells),
                "bbox": {
                    "min_row": min(row for row, _ in cells),
                    "min_col": min(col for _, col in cells),
                    "max_row": max(row for row, _ in cells),
                    "max_col": max(col for _, col in cells),
                },
                "center": {
                    "row": sum(row for row, _ in cells) / len(cells),
                    "col": sum(col for _, col in cells) / len(cells),
                },
                "shape_signature": "unit",
                "canonical_shape_signature": "unit",
                "normalized_shape": cells,
                "holes": 0,
                "is_solid": True,
            }
        ]


def test_counterfactual_simulation_reuses_invariant_input_objects():
    extractor = CountingObjectExtractor()
    predictor = PositionPredictor(object_extractor=extractor)
    simulator = CounterfactualSimulator(predictor)

    simulator.simulate_position_counterfactuals(
        [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 1, 0], [0, 0, 0], [0, 0, 0]],
        operation="duplicate_object",
        position_rule={"placement_vector": {"delta_row": 0, "delta_col": 1}},
        search_radius=2,
    )

    assert extractor.extract_calls <= 2


def test_counterfactual_simulation_preserves_candidate_order_and_best_rule():
    input_grid = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
    expected_grid = [[1, 1, 0], [0, 0, 0], [0, 0, 0]]
    rule = {"placement_vector": {"delta_row": 0, "delta_col": 1}}

    baseline = CounterfactualSimulator(
        PositionPredictor()
    ).simulate_position_counterfactuals(
        input_grid,
        expected_grid,
        operation="duplicate_object",
        position_rule=rule,
        search_radius=2,
    )

    repaired = CounterfactualSimulator(
        PositionPredictor()
    ).simulate_position_counterfactuals(
        input_grid,
        expected_grid,
        operation="duplicate_object",
        position_rule=rule,
        search_radius=2,
    )

    assert [item["placement_vector"] for item in repaired["candidates"]] == [
        item["placement_vector"] for item in baseline["candidates"]
    ]
    assert repaired["best_counterfactual"] == baseline["best_counterfactual"]
    assert repaired["recommended_position_rule"] == baseline["recommended_position_rule"]


def test_precomputed_invariant_state_is_not_mutated_across_candidates():
    predictor = PositionPredictor()
    normalized = [[1, 0, 0], [0, 0, 0], [0, 0, 0]]
    input_objects = predictor.object_extractor.extract_objects(normalized)

    predictor.predict_positioned_operation(
        normalized,
        "duplicate_object",
        {"placement_vector": {"delta_row": 0, "delta_col": 1}},
        normalized_input_grid=normalized,
        input_objects=input_objects,
    )
    first_snapshot = (normalized, input_objects)

    predictor.predict_positioned_operation(
        normalized,
        "duplicate_object",
        {"placement_vector": {"delta_row": 1, "delta_col": 0}},
        normalized_input_grid=normalized,
        input_objects=input_objects,
    )

    assert first_snapshot == (normalized, input_objects)


def test_counterfactual_simulation_reports_candidate_vector_progress(
    tmp_path,
    monkeypatch,
):
    monkeypatch.setenv(
        "NEXRYN_LOCALIZATION_TELEMETRY_PATH",
        str(tmp_path / "counterfactuals.jsonl"),
    )
    simulator = CounterfactualSimulator(PositionPredictor())

    simulator.simulate_position_counterfactuals(
        [[1, 0, 0], [0, 0, 0], [0, 0, 0]],
        [[1, 1, 0], [0, 0, 0], [0, 0, 0]],
        operation="duplicate_object",
        position_rule={"placement_vector": {"delta_row": 0, "delta_col": 1}},
        search_radius=1,
    )

    events = [
        json.loads(line)
        for line in (tmp_path / "counterfactuals.jsonl")
        .read_text(encoding="utf-8")
        .splitlines()
    ]
    candidate_events = [
        event
        for event in events
        if event["subcall_name"] == "position_counterfactual_candidate"
        and event["phase"] == "ENTER"
    ]
    assert len(candidate_events) == 9
    assert candidate_events[-1]["candidate_index"] == 9
    assert candidate_events[-1]["candidate_count"] == 9
