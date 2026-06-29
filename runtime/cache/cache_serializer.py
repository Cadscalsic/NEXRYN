from __future__ import annotations

from copy import deepcopy
from typing import Any


class CacheSerializer:
    HEAVY_KEYS = {
        "input_grid",
        "output_grid",
        "predicted_grid",
        "simulation_trace",
        "execution_trace",
        "runtime_context",
        "full_runtime_context",
        "dependency_evidence",
    }

    def __init__(self) -> None:
        self.heavy_objects_removed = 0

    def compact(self, value: Any) -> Any:
        return self._compact(deepcopy(value))

    def report(self) -> dict[str, Any]:
        return {
            "system": "cache_serializer",
            "heavy_objects_removed": self.heavy_objects_removed,
        }

    def _compact(self, value: Any) -> Any:
        if isinstance(value, dict):
            compacted = {}
            for key, item in value.items():
                if key == "counterfactual_candidates":
                    self.heavy_objects_removed += 1
                    compacted["counterfactual_candidates_summary"] = (
                        self._counterfactual_summary(item)
                    )
                    continue
                if key in self.HEAVY_KEYS:
                    self.heavy_objects_removed += 1
                    compacted[f"{key}_summary"] = self._summary(item)
                    continue
                compacted[key] = self._compact(item)
            return compacted
        if isinstance(value, list):
            return [self._compact(item) for item in value]
        return value

    def _summary(self, value: Any) -> dict[str, Any]:
        if isinstance(value, list):
            return {"type": "list", "item_count": len(value)}
        if isinstance(value, dict):
            return {
                "type": "dict",
                "key_count": len(value),
                "keys": list(value.keys())[:5],
            }
        return {"type": type(value).__name__}

    def _counterfactual_summary(self, value: Any) -> dict[str, Any]:
        candidates = value if isinstance(value, list) else []
        best = None
        best_accuracy = None
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            accuracy = candidate.get("prediction_accuracy")
            if accuracy is None:
                prediction = candidate.get("prediction_report", {})
                if isinstance(prediction, dict):
                    accuracy = prediction.get("prediction_accuracy")
            try:
                accuracy = float(accuracy)
            except (TypeError, ValueError):
                accuracy = 0.0
            if best_accuracy is None or accuracy > best_accuracy:
                best_accuracy = accuracy
                best = candidate
        summary = {"candidate_count": len(candidates)}
        if best is not None:
            summary.update({
                "best_accuracy": best_accuracy,
                "best_direction": best.get("direction")
                or best.get("placement_direction"),
                "best_operation": best.get("operation")
                or best.get("primitive")
                or best.get("winning_primitive"),
            })
            summary = {
                key: item
                for key, item in summary.items()
                if item is not None
            }
        return summary


__all__ = ["CacheSerializer"]
