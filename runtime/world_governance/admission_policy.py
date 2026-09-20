"""Admission policy for concepts, contexts, strategies, and programs."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping

from runtime.world_governance.constitutional_identity import (
    PROTECTED_CORE_NAMES,
)
from runtime.world_governance.evolution_policy import evolution_policy
from runtime.world_governance.world_state import ADMISSION_LEVELS


@dataclass
class AdmissionDecision:
    candidate_name: str
    candidate_type: str
    admission_level: str
    allowed: bool
    reason: str
    identity_risk: float
    truth_risk: float
    governance_risk: float
    evolution_value: float
    required_observations: int

    def as_dict(self) -> dict:
        return asdict(self)


class AdmissionPolicy:
    def evaluate(
        self,
        candidate: Mapping[str, Any] | Any,
        candidate_type: str = "concept",
    ) -> AdmissionDecision:
        data = self._data(candidate)
        name = self._name(data, candidate)
        candidate_type = str(data.get("candidate_type") or candidate_type)
        requested_level = str(data.get("admission_level") or "CANDIDATE")
        if requested_level not in ADMISSION_LEVELS:
            requested_level = "CANDIDATE"

        identity_risk = self._risk(data, "identity_risk")
        truth_risk = self._risk(data, "truth_risk")
        governance_risk = self._risk(data, "governance_risk")
        evolution = evolution_policy.evaluate(data)
        protected_core_touched = self.touches_protected_core(data)

        if protected_core_touched:
            return AdmissionDecision(
                name,
                candidate_type,
                "OUTSIDE_WORLD",
                False,
                "candidate_attempts_to_modify_protected_core",
                max(identity_risk, 1.0),
                max(truth_risk, 1.0),
                max(governance_risk, 1.0),
                evolution["evolution_value"],
                999,
            )

        if requested_level == "LOCKED_CORE":
            return AdmissionDecision(
                name,
                candidate_type,
                "IDENTITY_SUPPORTING_COMPONENT",
                False,
                "locked_core_requires_strict_governance_and_manual_review",
                max(identity_risk, 0.8),
                truth_risk,
                max(governance_risk, 0.8),
                evolution["evolution_value"],
                100,
            )

        if max(identity_risk, truth_risk, governance_risk) >= 0.75:
            return AdmissionDecision(
                name,
                candidate_type,
                "OUTSIDE_WORLD",
                False,
                "candidate_risk_exceeds_world_admission_threshold",
                identity_risk,
                truth_risk,
                governance_risk,
                evolution["evolution_value"],
                25,
            )

        if not evolution["allowed"]:
            return AdmissionDecision(
                name,
                candidate_type,
                "CANDIDATE",
                False,
                evolution["reason"],
                identity_risk,
                truth_risk,
                governance_risk,
                evolution["evolution_value"],
                5,
            )

        level = self._bounded_level(data, requested_level, candidate_type)
        return AdmissionDecision(
            name,
            candidate_type,
            level,
            True,
            "candidate_allowed_for_observed_world_participation",
            identity_risk,
            truth_risk,
            governance_risk,
            evolution["evolution_value"],
            self._required_observations(level),
        )

    def evaluate_candidate(
        self,
        candidate: Mapping[str, Any] | Any,
        candidate_type: str = "concept",
    ) -> AdmissionDecision:
        return self.evaluate(candidate, candidate_type)

    def touches_protected_core(self, data: Mapping[str, Any]) -> bool:
        touched = set()
        for key in ("modifies", "targets", "overrides", "weakens"):
            values = data.get(key, []) or []
            if isinstance(values, str):
                values = [values]
            touched.update(str(value).strip().lower() for value in values)
        direct_names = set(str(key).lower() for key in data.keys())
        return bool((touched | direct_names) & PROTECTED_CORE_NAMES)

    def _bounded_level(
        self,
        data: Mapping[str, Any],
        requested_level: str,
        candidate_type: str,
    ) -> str:
        observations = int(self._number(data.get("successful_observations")))
        stable = data.get("stable") is True
        reusable = data.get("reusable") is True
        identity_supporting = data.get("identity_supporting") is True

        if requested_level in {"OUTSIDE_WORLD", "CANDIDATE"}:
            return "CANDIDATE"
        if requested_level == "OBSERVED_USEFUL" and observations >= 1:
            return "OBSERVED_USEFUL"
        if (
            requested_level == "TRUSTED_TOOL"
            and candidate_type in {"strategy", "program"}
            and reusable
            and observations >= 3
        ):
            return "TRUSTED_TOOL"
        if requested_level == "WORLD_CITIZEN" and stable and observations >= 5:
            return "WORLD_CITIZEN"
        if (
            requested_level == "IDENTITY_SUPPORTING_COMPONENT"
            and identity_supporting
            and stable
            and observations >= 10
        ):
            return "IDENTITY_SUPPORTING_COMPONENT"
        return "CANDIDATE"

    def _required_observations(self, level: str) -> int:
        return {
            "CANDIDATE": 1,
            "OBSERVED_USEFUL": 3,
            "TRUSTED_TOOL": 5,
            "WORLD_CITIZEN": 10,
            "IDENTITY_SUPPORTING_COMPONENT": 25,
        }.get(level, 1)

    def _name(self, data: Mapping[str, Any], candidate: Any) -> str:
        return str(
            data.get("candidate_name")
            or data.get("name")
            or getattr(candidate, "candidate_name", None)
            or getattr(candidate, "name", None)
            or "unnamed_candidate"
        )

    def _risk(self, data: Mapping[str, Any], key: str) -> float:
        return min(1.0, max(0.0, self._number(data.get(key))))

    def _number(self, value: Any) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _data(self, value: Mapping[str, Any] | Any) -> dict[str, Any]:
        if isinstance(value, Mapping):
            return dict(value)
        keys = (
            "candidate_name",
            "name",
            "candidate_type",
            "admission_level",
            "identity_risk",
            "truth_risk",
            "governance_risk",
            "successful_observations",
            "stable",
            "reusable",
            "identity_supporting",
            "modifies",
            "targets",
            "overrides",
            "weakens",
            "improves",
        )
        return {
            key: getattr(value, key)
            for key in keys
            if hasattr(value, key)
        }


admission_policy = AdmissionPolicy()


__all__ = [
    "AdmissionDecision",
    "AdmissionPolicy",
    "admission_policy",
]
