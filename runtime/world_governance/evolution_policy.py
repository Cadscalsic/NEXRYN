"""Evolution permission policy for NEXRYN world governance."""

from __future__ import annotations

from typing import Any, Mapping


EVOLUTION_IMPROVEMENT_KEYS: tuple[str, ...] = (
    "reasoning_accuracy",
    "generalization",
    "memory_reuse",
    "strategy_reuse",
    "runtime_efficiency",
    "conceptual_diversity",
    "contextual_understanding",
    "process_understanding",
)

NON_WEAKENING_KEYS: tuple[str, ...] = (
    "truth_priority",
    "identity_continuity",
    "locked_truth_integrity",
    "security",
    "governance",
    "human_support_mission",
)


class EvolutionPolicy:
    def evaluate(self, candidate: Mapping[str, Any] | Any) -> dict[str, Any]:
        data = self._data(candidate)
        improvements = [
            key for key in EVOLUTION_IMPROVEMENT_KEYS
            if self._number(data.get(key)) > 0.0
            or key in set(data.get("improves", []) or [])
        ]
        weakened = [
            key for key in NON_WEAKENING_KEYS
            if data.get(f"weakens_{key}") is True
            or key in set(data.get("weakens", []) or [])
        ]
        evolution_value = max(
            [self._number(data.get(key)) for key in EVOLUTION_IMPROVEMENT_KEYS]
            + [0.0]
        )
        if improvements and evolution_value == 0.0:
            evolution_value = 0.5

        return {
            "allowed": bool(improvements) and not weakened,
            "evolution_value": min(1.0, max(0.0, evolution_value)),
            "improvements": improvements,
            "weakened_principles": weakened,
            "reason": self._reason(improvements, weakened),
        }

    def _reason(self, improvements: list[str], weakened: list[str]) -> str:
        if weakened:
            return "candidate_weakens_non_negotiable_governance_or_identity"
        if not improvements:
            return "candidate_has_no_clear_evolution_value"
        return "candidate_supports_bounded_cognitive_evolution"

    def _data(self, value: Mapping[str, Any] | Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        data = {}
        for key in EVOLUTION_IMPROVEMENT_KEYS + NON_WEAKENING_KEYS:
            if hasattr(value, key):
                data[key] = getattr(value, key)
        for key in ("improves", "weakens"):
            if hasattr(value, key):
                data[key] = getattr(value, key)
        return data

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


evolution_policy = EvolutionPolicy()


__all__ = [
    "EVOLUTION_IMPROVEMENT_KEYS",
    "NON_WEAKENING_KEYS",
    "EvolutionPolicy",
    "evolution_policy",
]
