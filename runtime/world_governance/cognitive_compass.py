"""Cognitive compass for current and desired long-term state."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.long_term_objectives import (
    DEFAULT_LONG_TERM_OBJECTIVES,
    LongTermObjectives,
)


@dataclass
class CognitiveCompassState:
    current_cognitive_state: dict[str, float]
    desired_cognitive_state: dict[str, float]
    objective_distance: dict[str, float]
    trajectory_confidence: float

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class CognitiveCompass:
    def assess(
        self,
        runtime_context: Mapping[str, Any] | None = None,
        objectives: LongTermObjectives | None = None,
    ) -> CognitiveCompassState:
        context = dict(runtime_context or {})
        active_objectives = objectives or DEFAULT_LONG_TERM_OBJECTIVES
        desired = {
            key: min(1.0, max(0.05, weight * 4.0))
            for key, weight in active_objectives.normalized().as_dict().items()
        }
        current = {
            key: self._metric(context, key)
            for key in desired
        }
        distance = {
            key: max(0.0, desired[key] - current.get(key, 0.0))
            for key in desired
        }
        average_distance = sum(distance.values()) / max(1, len(distance))
        evidence_signal = self._metric(context, "evidence_quality", default=0.5)
        confidence = min(1.0, max(0.0, 1.0 - average_distance * 0.6 + evidence_signal * 0.2))
        return CognitiveCompassState(current, desired, distance, confidence)

    def _metric(self, context: Mapping[str, Any], key: str, default: float = 0.0) -> float:
        aliases = {
            "strategy_reuse": "strategy_reuse_rate",
            "context_reuse": "context_reuse_rate",
            "memory_efficiency": "memory_efficiency",
            "runtime_efficiency": "runtime_efficiency",
            "process_understanding": "process_understanding",
            "causal_reasoning": "causal_reasoning",
            "cognitive_diversity": "diversity_score",
        }
        value = context.get(key, context.get(aliases.get(key, key), default))
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return default


cognitive_compass = CognitiveCompass()


__all__ = [
    "CognitiveCompass",
    "CognitiveCompassState",
    "cognitive_compass",
]
