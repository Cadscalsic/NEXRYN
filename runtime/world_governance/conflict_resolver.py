"""Conflict detection and trade-off analysis for parliament deliberation."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.deliberation_engine import RepresentativeOpinion


class ConflictResolver:
    def analyze(
        self,
        proposal: Mapping[str, Any],
        opinions: list[RepresentativeOpinion],
    ) -> dict[str, Any]:
        conflicts: list[dict[str, Any]] = []
        recommendation_set = {opinion.recommendation for opinion in opinions}

        if {"SUPPORT", "REJECT"} <= recommendation_set or {
            "SUPPORT_WITH_LIMITS",
            "REJECT",
        } <= recommendation_set:
            conflicts.append({
                "conflict_type": "exploration_vs_stability",
                "tradeoff": "supporting representatives see value while rejecting representatives see unacceptable risk",
            })

        if self._number(proposal.get("expected_efficiency_gain")) > 0.5 and self._number(proposal.get("conceptual_diversity_gain")) < 0.2:
            conflicts.append({
                "conflict_type": "efficiency_vs_diversity",
                "tradeoff": "efficiency gains may narrow cognitive alternatives",
            })

        if self._number(proposal.get("expected_accuracy_gain")) > 0.6 and self._number(proposal.get("resource_cost")) > 0.5:
            conflicts.append({
                "conflict_type": "accuracy_vs_resource_cost",
                "tradeoff": "accuracy gain may consume excessive cognitive budget",
            })

        if self._number(proposal.get("strategy_reuse")) > 0.6 and self._number(proposal.get("innovation_value")) > 0.5:
            conflicts.append({
                "conflict_type": "reuse_vs_innovation",
                "tradeoff": "reuse pressure and innovation pressure both have evidence",
            })

        return {
            "conflicts": conflicts,
            "conflict_count": len(conflicts),
        }

    def _number(self, value: Any) -> float:
        try:
            return min(1.0, max(0.0, float(value)))
        except (TypeError, ValueError):
            return 0.0


conflict_resolver = ConflictResolver()


__all__ = [
    "ConflictResolver",
    "conflict_resolver",
]
