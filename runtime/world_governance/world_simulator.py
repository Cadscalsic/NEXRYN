"""Lightweight simulation for candidate cognitive futures."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.cognitive_risk_estimator import (
    cognitive_risk_estimator,
)


RECOMMENDATIONS: tuple[str, ...] = (
    "ADOPT",
    "ADOPT_WITH_LIMITS",
    "TEST_IN_SANDBOX",
    "QUARANTINE",
    "REJECT",
    "REQUIRE_MORE_EVIDENCE",
)


@dataclass
class CandidateWorld:
    world_id: str
    candidate_name: str
    candidate_type: str
    proposed_admission_level: str
    expected_accuracy_gain: float
    expected_efficiency_gain: float
    expected_generalization_gain: float
    conceptual_diversity_gain: float
    identity_risk: float
    truth_risk: float
    governance_risk: float
    resource_cost: float
    recommendation: str

    @property
    def world_score(self) -> float:
        return score_world(self)

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["world_score"] = self.world_score
        return payload


def score_world(world: CandidateWorld) -> float:
    return (
        world.expected_accuracy_gain * 0.25
        + world.expected_efficiency_gain * 0.20
        + world.expected_generalization_gain * 0.25
        + world.conceptual_diversity_gain * 0.10
        - world.identity_risk * 0.30
        - world.truth_risk * 0.30
        - world.governance_risk * 0.20
        - world.resource_cost * 0.10
    )


class WorldSimulator:
    def simulate(
        self,
        candidate: Mapping[str, Any] | Any,
        future: Mapping[str, Any],
    ) -> CandidateWorld:
        data = self._data(candidate)
        risks = cognitive_risk_estimator.estimate(data)
        action = str(future.get("future_type") or "observe_candidate")
        multiplier = self._future_multiplier(action)

        identity_risk = self._bounded(risks["identity_risk"] * multiplier["risk"])
        truth_risk = self._bounded(risks["truth_risk"] * multiplier["risk"])
        governance_risk = self._bounded(
            risks["governance_risk"] * multiplier["governance"]
        )
        resource_cost = self._bounded(
            self._number(data.get("resource_cost"))
            + risks["resource_risk"] * 0.5
            + multiplier["cost"]
        )

        world = CandidateWorld(
            world_id=str(future.get("world_id") or action),
            candidate_name=self._candidate_name(data),
            candidate_type=str(data.get("candidate_type") or future.get("candidate_type") or "concept"),
            proposed_admission_level=str(
                future.get("proposed_admission_level")
                or data.get("admission_level")
                or "CANDIDATE"
            ),
            expected_accuracy_gain=self._gain(data, "expected_accuracy_gain", "reasoning_accuracy") * multiplier["gain"],
            expected_efficiency_gain=self._gain(data, "expected_efficiency_gain", "runtime_efficiency") * multiplier["efficiency"],
            expected_generalization_gain=self._gain(data, "expected_generalization_gain", "generalization") * multiplier["gain"],
            conceptual_diversity_gain=self._gain(data, "conceptual_diversity_gain", "conceptual_diversity") * multiplier["diversity"],
            identity_risk=identity_risk,
            truth_risk=truth_risk,
            governance_risk=governance_risk,
            resource_cost=resource_cost,
            recommendation="REQUIRE_MORE_EVIDENCE",
        )
        world.recommendation = self._recommend(world, risks)
        return world

    def _recommend(self, world: CandidateWorld, risks: Mapping[str, float]) -> str:
        if risks.get("protected_core_touched", 0.0) >= 1.0:
            return "REJECT"
        if max(world.identity_risk, world.truth_risk) >= 0.75:
            return "QUARANTINE"
        if world.governance_risk >= 0.75:
            return "QUARANTINE"
        if world.resource_cost >= 0.85:
            return "REQUIRE_MORE_EVIDENCE"
        if world.world_score >= 0.22 and max(world.identity_risk, world.truth_risk) <= 0.25:
            return "ADOPT"
        if world.world_score >= 0.10 and max(world.identity_risk, world.truth_risk, world.governance_risk) <= 0.50:
            return "ADOPT_WITH_LIMITS"
        if world.world_score >= 0.0:
            return "TEST_IN_SANDBOX"
        if max(world.identity_risk, world.truth_risk, world.governance_risk) >= 0.60:
            return "QUARANTINE"
        return "REQUIRE_MORE_EVIDENCE"

    def _future_multiplier(self, action: str) -> dict[str, float]:
        multipliers = {
            "reuse_existing_strategy": {
                "gain": 0.75,
                "efficiency": 1.20,
                "diversity": 0.50,
                "risk": 0.75,
                "governance": 0.80,
                "cost": 0.05,
            },
            "promote_new_strategy": {
                "gain": 1.10,
                "efficiency": 1.00,
                "diversity": 0.80,
                "risk": 1.20,
                "governance": 1.25,
                "cost": 0.20,
            },
            "admit_new_context": {
                "gain": 0.85,
                "efficiency": 0.75,
                "diversity": 1.15,
                "risk": 0.90,
                "governance": 0.90,
                "cost": 0.15,
            },
            "merge_similar_concepts": {
                "gain": 0.70,
                "efficiency": 1.15,
                "diversity": 0.70,
                "risk": 1.05,
                "governance": 1.00,
                "cost": 0.15,
            },
            "keep_candidate_in_quarantine": {
                "gain": 0.10,
                "efficiency": 0.10,
                "diversity": 0.20,
                "risk": 0.40,
                "governance": 0.50,
                "cost": 0.05,
            },
            "freeze_existing_truth": {
                "gain": 0.05,
                "efficiency": 0.20,
                "diversity": 0.10,
                "risk": 0.35,
                "governance": 0.45,
                "cost": 0.05,
            },
            "expand_training_curriculum": {
                "gain": 0.80,
                "efficiency": 0.60,
                "diversity": 1.20,
                "risk": 0.80,
                "governance": 0.85,
                "cost": 0.30,
            },
        }
        return multipliers.get(action, {
            "gain": 0.50,
            "efficiency": 0.50,
            "diversity": 0.50,
            "risk": 1.00,
            "governance": 1.00,
            "cost": 0.10,
        })

    def _gain(self, data: Mapping[str, Any], primary: str, fallback: str) -> float:
        value = data.get(primary)
        if value is None:
            value = data.get(fallback)
        return self._bounded(self._number(value))

    def _candidate_name(self, data: Mapping[str, Any]) -> str:
        return str(data.get("candidate_name") or data.get("name") or "unnamed_candidate")

    def _bounded(self, value: float) -> float:
        return min(1.0, max(0.0, value))

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _data(self, value: Mapping[str, Any] | Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        data = {}
        for key in dir(value):
            if key.startswith("_"):
                continue
            item = getattr(value, key)
            if not callable(item):
                data[key] = item
        return data


world_simulator = WorldSimulator()


__all__ = [
    "CandidateWorld",
    "RECOMMENDATIONS",
    "WorldSimulator",
    "score_world",
    "world_simulator",
]
