from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping

import numpy as np


class PostRepairResidualAnalyzer:
    """Recompute residual evidence from the latest validated repair output."""

    def analyze(
        self,
        repaired_prediction: Any,
        target_output: Any,
        *,
        previous_residual: Mapping[str, Any] | None = None,
        repair_iteration_id: str = "",
    ) -> dict[str, Any]:
        previous = previous_residual if isinstance(previous_residual, Mapping) else {}
        predicted = np.array(repaired_prediction)
        target = np.array(target_output)
        locations = []
        residual_type = "none"
        probable_root_cause = "none"
        if predicted.size and target.size and predicted.shape == target.shape:
            differences = np.argwhere(predicted != target)
            locations = [[int(row), int(col)] for row, col in differences]
            if locations:
                residual_type = "localized_color_residual"
                probable_root_cause = "localized_prediction_mismatch"
        elif target.size or predicted.size:
            locations = []
            residual_type = "shape_or_alignment_residual"
            probable_root_cause = "output_shape_mismatch"
        count = len(locations) if predicted.shape == target.shape else int(max(predicted.size, target.size))
        previous_locations = {
            tuple(item)
            for item in previous.get("residual_locations", [])
            if isinstance(item, list) and len(item) == 2
        }
        current_locations = {tuple(item) for item in locations}
        previous_count = int(previous.get("residual_difference_count", count) or 0)
        fingerprint = _fingerprint({
            "count": count,
            "locations": locations,
            "type": residual_type,
        })
        return {
            "repair_iteration_id": repair_iteration_id,
            "residual_difference_count": count,
            "residual_locations": locations,
            "residual_type": residual_type,
            "probable_root_cause": probable_root_cause,
            "future_learning_priority": (
                "refine_residual_localization" if count else "none"
            ),
            "residual_changed": (
                count != previous_count
                or current_locations != previous_locations
                or residual_type != previous.get("residual_type")
            ),
            "previous_residual_count": previous_count,
            "residual_reduction": max(0, previous_count - count),
            "removed_residual_locations": [
                list(item) for item in sorted(previous_locations - current_locations)
            ],
            "remaining_residual_locations": [
                list(item) for item in sorted(previous_locations & current_locations)
            ],
            "new_residual_locations": [
                list(item) for item in sorted(current_locations - previous_locations)
            ],
            "residual_fingerprint": fingerprint,
            "actionable": count > 0 and residual_type == "localized_color_residual",
        }


def _fingerprint(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:16]


post_repair_residual_analyzer = PostRepairResidualAnalyzer()


__all__ = ["PostRepairResidualAnalyzer", "post_repair_residual_analyzer"]
