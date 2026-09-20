"""Rank candidate worlds for bounded cognitive evolution."""

from __future__ import annotations

from runtime.world_governance.world_simulator import CandidateWorld


class EvolutionPathRanker:
    def rank(self, worlds: list[CandidateWorld]) -> list[CandidateWorld]:
        return sorted(
            worlds,
            key=self._rank_key,
            reverse=True,
        )

    def best(self, worlds: list[CandidateWorld]) -> CandidateWorld | None:
        ranked = self.rank(worlds)
        return ranked[0] if ranked else None

    def _rank_key(self, world: CandidateWorld) -> tuple[float, float, float, float, float, float]:
        useful_gain = (
            world.expected_accuracy_gain
            + world.expected_generalization_gain
            + world.expected_efficiency_gain
            + world.conceptual_diversity_gain * 0.5
        )
        risk_gate = max(world.identity_risk, world.truth_risk)
        safety_priority = 1.0
        if risk_gate >= 0.60:
            safety_priority = 0.0
            useful_gain -= 2.0
        if world.recommendation in {"REJECT", "QUARANTINE"}:
            safety_priority = 0.0
            useful_gain -= 1.0

        return (
            safety_priority,
            world.world_score,
            useful_gain,
            -world.identity_risk,
            -world.truth_risk,
            -world.resource_cost,
        )


evolution_path_ranker = EvolutionPathRanker()


__all__ = [
    "EvolutionPathRanker",
    "evolution_path_ranker",
]
