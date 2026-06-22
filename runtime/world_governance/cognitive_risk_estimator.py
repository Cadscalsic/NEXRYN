"""Lightweight cognitive risk estimation for candidate worlds."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.world_governance.admission_policy import admission_policy


class CognitiveRiskEstimator:
    def estimate(self, candidate: Mapping[str, Any] | Any) -> dict[str, float]:
        data = self._data(candidate)
        protected_core_touched = admission_policy.touches_protected_core(data)

        identity_risk = self._risk(data, "identity_risk")
        truth_risk = self._risk(data, "truth_risk")
        governance_risk = self._risk(data, "governance_risk")
        resource_risk = self._risk(
            data,
            "resource_risk",
            fallback_key="resource_cost",
        )
        reward_hacking_risk = self._risk(data, "reward_hacking_risk")
        overfitting_risk = self._risk(data, "overfitting_risk")

        if protected_core_touched:
            identity_risk = max(identity_risk, 1.0)
            truth_risk = max(truth_risk, 1.0)
            governance_risk = max(governance_risk, 1.0)

        if data.get("optimizes_reward_directly") is True:
            reward_hacking_risk = max(reward_hacking_risk, 0.75)

        if data.get("narrow_task_fit") is True:
            overfitting_risk = max(overfitting_risk, 0.65)

        return {
            "identity_risk": identity_risk,
            "truth_risk": truth_risk,
            "governance_risk": governance_risk,
            "resource_risk": resource_risk,
            "reward_hacking_risk": reward_hacking_risk,
            "overfitting_risk": overfitting_risk,
            "protected_core_touched": 1.0 if protected_core_touched else 0.0,
        }

    def _risk(
        self,
        data: Mapping[str, Any],
        key: str,
        fallback_key: str | None = None,
    ) -> float:
        value = data.get(key)
        if value is None and fallback_key is not None:
            value = data.get(fallback_key)
        return min(1.0, max(0.0, self._number(value)))

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


cognitive_risk_estimator = CognitiveRiskEstimator()


__all__ = [
    "CognitiveRiskEstimator",
    "cognitive_risk_estimator",
]
