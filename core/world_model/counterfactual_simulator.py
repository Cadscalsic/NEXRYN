"""Counterfactual simulation for position-sensitive ARC operations."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from core.epistemic_models import clamp
from core.world_model.position_predictor import PositionPredictor


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
    ) -> dict[str, Any]:
        base_rule = dict(position_rule or {})
        base_vector = dict(base_rule.get("placement_vector", {}))
        candidate_vectors = self._candidate_vectors(base_vector, search_radius)
        candidates = []

        for vector in candidate_vectors:
            candidate_rule = {
                **base_rule,
                "placement_vector": vector,
            }
            prediction = self.position_predictor.predict_positioned_operation(
                input_grid,
                operation,
                candidate_rule,
            )
            mismatch = self.position_predictor.diagnose_position_mismatch(
                prediction["predicted_grid"],
                expected_grid,
            )
            total_cells = self._cell_count(expected_grid)
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

        candidates.sort(
            key=lambda item: (item["accuracy"], -item["difference_count"]),
            reverse=True,
        )
        best = candidates[0] if candidates else {}
        return {
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
