"""Counterfactual simulation for position-sensitive ARC operations."""

from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Mapping

from core.epistemic_models import clamp
from core.world_model.position_predictor import PositionPredictor
from runtime.telemetry.localization_progress import (
    emit as emit_localization_progress,
    grid_shape as telemetry_grid_shape,
    stable_id as telemetry_stable_id,
)
from runtime.telemetry.candidate_cost_profiler import build_profiler


class CounterfactualSimulator:
    """Try nearby placement alternatives before execution is authorized."""

    def __init__(self, position_predictor: PositionPredictor | None = None) -> None:
        self.position_predictor = position_predictor or PositionPredictor()

    def simulate_position_counterfactuals(
        self,
        input_grid: Any,
        expected_grid: Any,
        operation: str = "duplicate_object",
        position_rule: Mapping[str, Any] | None = None,
        search_radius: int = 1,
        telemetry_parent_call_id: str | None = None,
        telemetry_parent_started_at: float | None = None,
        runtime_context: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        base_rule = dict(position_rule or {})
        base_vector = dict(base_rule.get("placement_vector", {}))
        candidate_vectors = self._candidate_vectors(base_vector, search_radius)
        normalized_input = self.position_predictor.object_extractor.normalize_grid(
            input_grid
        )
        input_objects = self.position_predictor.object_extractor.extract_objects(
            normalized_input
        )
        expected_normalized = self.position_predictor.object_extractor.normalize_grid(
            expected_grid
        )
        expected_scene = self.position_predictor.scene_graph_engine.build_scene_graph(
            expected_normalized
        )
        total_cells = sum(len(row) for row in expected_normalized)
        candidates = []
        started_at = time.perf_counter()
        parent_call_id = telemetry_parent_call_id or "position_counterfactuals"
        vector_count = len(candidate_vectors)
        candidate_cost_profiler = build_profiler(
            runtime_context,
            candidate_count=vector_count,
        )

        for candidate_index, vector in enumerate(candidate_vectors, 1):
            if candidate_cost_profiler is not None:
                candidate_cost_profiler.candidate_started(candidate_index)
            candidate_call_id = (
                f"{parent_call_id}:candidate:{candidate_index}"
            )
            emit_localization_progress(
                phase="ENTER",
                subcall_name="position_counterfactual_candidate",
                call_id=candidate_call_id,
                parent_call_id=parent_call_id,
                started_at=started_at,
                parent_started_at=telemetry_parent_started_at or started_at,
                candidate_index=candidate_index,
                candidate_count=vector_count,
                vector_fingerprint=telemetry_stable_id(vector),
                input_grid_shape=telemetry_grid_shape(normalized_input),
                target_grid_shape=telemetry_grid_shape(expected_normalized),
            )
            candidate_rule = {
                **base_rule,
                "placement_vector": vector,
            }
            prediction_call_id = f"{candidate_call_id}:position_predictor"
            emit_localization_progress(
                phase="ENTER",
                subcall_name="position_predictor",
                call_id=prediction_call_id,
                parent_call_id=candidate_call_id,
                started_at=started_at,
                parent_started_at=telemetry_parent_started_at or started_at,
                candidate_index=candidate_index,
                predictor_call_count=candidate_index,
            )
            if candidate_cost_profiler is not None:
                with candidate_cost_profiler.prediction_timer():
                    prediction = self.position_predictor.predict_positioned_operation(
                        input_grid,
                        operation,
                        candidate_rule,
                        normalized_input_grid=normalized_input,
                        input_objects=input_objects,
                    )
            else:
                prediction = self.position_predictor.predict_positioned_operation(
                    input_grid,
                    operation,
                    candidate_rule,
                    normalized_input_grid=normalized_input,
                    input_objects=input_objects,
                )
            emit_localization_progress(
                phase="EXIT",
                subcall_name="position_predictor",
                call_id=prediction_call_id,
                parent_call_id=candidate_call_id,
                started_at=started_at,
                parent_started_at=telemetry_parent_started_at or started_at,
                candidate_index=candidate_index,
                prediction_state=prediction.get("prediction_state"),
            )
            evaluation_call_id = f"{candidate_call_id}:prediction_evaluation"
            emit_localization_progress(
                phase="ENTER",
                subcall_name="prediction_evaluation",
                call_id=evaluation_call_id,
                parent_call_id=candidate_call_id,
                started_at=started_at,
                parent_started_at=telemetry_parent_started_at or started_at,
                candidate_index=candidate_index,
                simulation_count=candidate_index,
            )
            if candidate_cost_profiler is not None:
                with candidate_cost_profiler.evaluation_timer():
                    mismatch = self.position_predictor.diagnose_position_mismatch(
                        prediction["predicted_grid"],
                        expected_grid,
                        expected_normalized_grid=expected_normalized,
                        expected_scene=expected_scene,
                        candidate_cost_profiler=candidate_cost_profiler,
                    )
            else:
                mismatch = self.position_predictor.diagnose_position_mismatch(
                    prediction["predicted_grid"],
                    expected_grid,
                    expected_normalized_grid=expected_normalized,
                    expected_scene=expected_scene,
                )
            emit_localization_progress(
                phase="EXIT",
                subcall_name="prediction_evaluation",
                call_id=evaluation_call_id,
                parent_call_id=candidate_call_id,
                started_at=started_at,
                parent_started_at=telemetry_parent_started_at or started_at,
                candidate_index=candidate_index,
                difference_count=mismatch["difference_count"],
                object_match_count=mismatch["object_match_count"],
            )
            if candidate_cost_profiler is not None:
                with candidate_cost_profiler.owner_timer("scoring"):
                    accuracy = clamp(
                        1.0 - mismatch["difference_count"] / max(total_cells, 1)
                    )
            else:
                accuracy = clamp(
                    1.0 - mismatch["difference_count"] / max(total_cells, 1)
                )
            candidates.append({
                "operation": operation,
                "placement_vector": vector,
                "predicted_grid": prediction["predicted_grid"],
                "accuracy": accuracy,
                "difference_count": mismatch["difference_count"],
                "mismatch": mismatch,
                "counterfactual_state": (
                    "POSITION_COUNTERFACTUAL_MATCH"
                    if mismatch["difference_count"] == 0
                    else "POSITION_COUNTERFACTUAL_MISMATCH"
                ),
            })
            emit_localization_progress(
                phase="EXIT",
                subcall_name="position_counterfactual_candidate",
                call_id=candidate_call_id,
                parent_call_id=parent_call_id,
                started_at=started_at,
                parent_started_at=telemetry_parent_started_at or started_at,
                candidate_index=candidate_index,
                candidate_count=vector_count,
                accuracy=accuracy,
                difference_count=mismatch["difference_count"],
            )
            if candidate_cost_profiler is not None:
                candidate_cost_profiler.candidate_completed(candidate_index)

        candidates.sort(
            key=lambda item: (item["accuracy"], -item["difference_count"]),
            reverse=True,
        )
        best = candidates[0] if candidates else {}
        report = {
            "system": "counterfactual_simulator",
            "mode": "position_counterfactuals",
            "operation": operation,
            "candidate_count": len(candidates),
            "best_counterfactual": best,
            "candidates": candidates,
            "localized_prediction_mismatch_resolved": (
                bool(best) and best.get("difference_count") == 0
            ),
            "recommended_position_rule": {
                **base_rule,
                "placement_vector": best.get("placement_vector", {}),
                "confidence": best.get("accuracy", 0.0),
            }
            if best
            else {},
        }
        if candidate_cost_profiler is not None:
            profile = candidate_cost_profiler.report()
            candidate_cost_profiler.flush()
            report["low_overhead_candidate_cost_profile"] = profile
        return report

    def _candidate_vectors(
        self,
        base_vector: Mapping[str, Any],
        search_radius: int,
    ) -> list[dict[str, Any]]:
        base_row = int(round(float(base_vector.get("delta_row", 0))))
        base_col = int(round(float(base_vector.get("delta_col", 0))))
        radius = max(int(search_radius or 0), 0)
        vectors = []
        seen = set()
        for d_row in range(base_row - radius, base_row + radius + 1):
            for d_col in range(base_col - radius, base_col + radius + 1):
                key = (d_row, d_col)
                if key in seen:
                    continue
                seen.add(key)
                vectors.append({
                    "delta_row": d_row,
                    "delta_col": d_col,
                    "axis": self._axis(d_row, d_col),
                    "direction": self._direction(d_row, d_col),
                })
        return vectors

    def _cell_count(self, grid: Any) -> int:
        normalized = self.position_predictor.object_extractor.normalize_grid(grid)
        return sum(len(row) for row in normalized)

    def _axis(self, delta_row: int, delta_col: int) -> str:
        if delta_row == 0 and delta_col == 0:
            return "same_position"
        if delta_row == 0:
            return "horizontal"
        if delta_col == 0:
            return "vertical"
        return "diagonal"

    def _direction(self, delta_row: int, delta_col: int) -> str:
        vertical = "down" if delta_row > 0 else "up" if delta_row < 0 else ""
        horizontal = "right" if delta_col > 0 else "left" if delta_col < 0 else ""
        return "_".join(part for part in [vertical, horizontal] if part) or "same"


__all__ = [
    "CounterfactualSimulator",
]
