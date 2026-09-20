"""Configurable long-term purpose objectives for NEXRYN."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping


@dataclass
class LongTermObjectives:
    generalization: float = 0.25
    process_understanding: float = 0.20
    strategy_reuse: float = 0.15
    context_reuse: float = 0.10
    memory_efficiency: float = 0.10
    runtime_efficiency: float = 0.10
    causal_reasoning: float = 0.05
    cognitive_diversity: float = 0.05

    def normalized(self) -> "LongTermObjectives":
        values = self.as_dict()
        total = sum(max(0.0, value) for value in values.values())
        if total <= 0.0:
            return LongTermObjectives()
        return LongTermObjectives(**{
            key: max(0.0, value) / total
            for key, value in values.items()
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


DEFAULT_LONG_TERM_OBJECTIVES = LongTermObjectives()


__all__ = [
    "DEFAULT_LONG_TERM_OBJECTIVES",
    "LongTermObjectives",
]
