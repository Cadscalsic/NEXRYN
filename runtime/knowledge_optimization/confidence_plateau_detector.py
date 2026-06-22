"""Detect confidence plateaus and terminate cognition."""

from __future__ import annotations

from typing import Any


class ConfidencePlateauDetector:
    def __init__(self, consecutive_cycles: int = 5, min_delta: float = 0.01) -> None:
        self.consecutive_cycles = int(consecutive_cycles)
        self.min_delta = float(min_delta)

    def evaluate(
        self,
        confidence_history: list[Any] | tuple[Any, ...],
        consecutive_cycles: int | None = None,
    ) -> dict[str, Any]:
        required = int(consecutive_cycles or self.consecutive_cycles)
        values = [self._number(value) for value in confidence_history]
        deltas = [
            abs(values[index] - values[index - 1])
            for index in range(1, len(values))
        ]
        recent = deltas[-required:]
        plateau = len(recent) >= required and all(delta < self.min_delta for delta in recent)
        return {
            "plateau_detected": plateau,
            "confidence_delta": recent[-1] if recent else 0.0,
            "consecutive_cycles": required,
            "terminate_reason": "COGNITIVE_PLATEAU" if plateau else None,
            "actions": (
                ["commit_best_candidate", "stop_reasoning", "release_resources", "shutdown_runtime"]
                if plateau
                else []
            ),
        }

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


confidence_plateau_detector = ConfidencePlateauDetector()


__all__ = [
    "ConfidencePlateauDetector",
    "confidence_plateau_detector",
]
