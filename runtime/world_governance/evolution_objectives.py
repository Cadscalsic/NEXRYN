"""Configurable long-term cognitive evolution objectives."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass
class EvolutionObjectives:
    reasoning_accuracy: float = 0.25
    generalization: float = 0.25
    strategy_reuse: float = 0.15
    memory_efficiency: float = 0.15
    contextual_understanding: float = 0.10
    cognitive_diversity: float = 0.05
    runtime_efficiency: float = 0.05

    def normalized(self) -> "EvolutionObjectives":
        total = sum(max(0.0, value) for value in self.as_dict().values())
        if total <= 0.0:
            return EvolutionObjectives()
        return EvolutionObjectives(**{
            key: max(0.0, value) / total
            for key, value in self.as_dict().items()
        })

    def score(self, values: Mapping[str, Any]) -> float:
        objectives = self.normalized().as_dict()
        return sum(
            weight * self._number(values.get(name))
            for name, weight in objectives.items()
        )

    def as_dict(self) -> dict[str, float]:
        return asdict(self)

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


DEFAULT_EVOLUTION_OBJECTIVES = EvolutionObjectives()


__all__ = [
    "DEFAULT_EVOLUTION_OBJECTIVES",
    "EvolutionObjectives",
]
