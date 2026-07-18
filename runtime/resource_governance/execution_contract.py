"""Canonical execution contracts and legacy alias migration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

from runtime.resource_governance.execution_policy import ExecutionPolicyName


LEGACY_MODE_ALIASES = {
    "fast": ExecutionPolicyName.LOW_LATENCY,
    "adaptive": ExecutionPolicyName.BALANCED,
    "deep": ExecutionPolicyName.MAX_ACCURACY,
    "research": ExecutionPolicyName.RESEARCH,
    "diagnostic": ExecutionPolicyName.DIAGNOSTIC,
    "training": ExecutionPolicyName.TRAINING,
}

SUPPORTED_POLICY_ALIASES = {
    "low-latency": ExecutionPolicyName.LOW_LATENCY,
    "low_latency": ExecutionPolicyName.LOW_LATENCY,
    "balanced": ExecutionPolicyName.BALANCED,
    "max-accuracy": ExecutionPolicyName.MAX_ACCURACY,
    "max_accuracy": ExecutionPolicyName.MAX_ACCURACY,
    "research": ExecutionPolicyName.RESEARCH,
    "diagnostic": ExecutionPolicyName.DIAGNOSTIC,
    "training": ExecutionPolicyName.TRAINING,
}


@dataclass(frozen=True)
class ExecutionContract:
    contract_id: str
    policy: ExecutionPolicyName
    latency_target: float = 30.0
    accuracy_target: float = 0.95
    confidence_target: float = 0.90
    resource_limits: dict[str, Any] = field(default_factory=dict)
    reporting_requirements: dict[str, Any] = field(default_factory=dict)
    persistence_requirements: dict[str, Any] = field(default_factory=dict)
    maintenance_permissions: dict[str, Any] = field(default_factory=dict)
    diagnostic_permissions: dict[str, Any] = field(default_factory=dict)
    research_permissions: dict[str, Any] = field(default_factory=dict)
    termination_preferences: dict[str, Any] = field(default_factory=dict)
    fallback_behavior: dict[str, Any] = field(default_factory=dict)
    requested_policy: str = "BALANCED"
    resolved_policy: ExecutionPolicyName = ExecutionPolicyName.BALANCED
    legacy_alias: str | None = None
    alias_warning: str | None = None
    resolution_reason: str = "explicit_policy"

    @classmethod
    def create(
        cls,
        policy: str | ExecutionPolicyName | None = None,
        legacy_mode: str | None = None,
        task_profile: Any | None = None,
        **overrides: Any,
    ) -> "ExecutionContract":
        resolved = resolve_policy(policy, legacy_mode, task_profile)
        policy_name = resolved["resolved_policy"]
        values = {
            "contract_id": f"contract-{uuid4()}",
            "policy": policy_name,
            "latency_target": _latency_for(policy_name),
            "accuracy_target": _accuracy_for(policy_name),
            "confidence_target": _confidence_for(policy_name),
            "resource_limits": {},
            "reporting_requirements": _reporting_for(policy_name),
            "persistence_requirements": _persistence_for(policy_name),
            "maintenance_permissions": _maintenance_for(policy_name),
            "diagnostic_permissions": {"allow_diagnostic_overhead": policy_name == ExecutionPolicyName.DIAGNOSTIC},
            "research_permissions": {"allow_research_replay": policy_name == ExecutionPolicyName.RESEARCH},
            "termination_preferences": {"immediate_exact_success": True},
            "fallback_behavior": {"policy_resolution_failure": "BALANCED"},
            "requested_policy": resolved["requested_policy"],
            "resolved_policy": policy_name,
            "legacy_alias": resolved["legacy_alias"],
            "alias_warning": resolved["alias_warning"],
            "resolution_reason": resolved["resolution_reason"],
        }
        values.update(overrides)
        return cls(**values)

    def as_dict(self) -> dict[str, Any]:
        return {
            "contract_id": self.contract_id,
            "policy": self.policy.value,
            "latency_target": self.latency_target,
            "accuracy_target": self.accuracy_target,
            "confidence_target": self.confidence_target,
            "resource_limits": dict(self.resource_limits),
            "reporting_requirements": dict(self.reporting_requirements),
            "persistence_requirements": dict(self.persistence_requirements),
            "maintenance_permissions": dict(self.maintenance_permissions),
            "diagnostic_permissions": dict(self.diagnostic_permissions),
            "research_permissions": dict(self.research_permissions),
            "termination_preferences": dict(self.termination_preferences),
            "fallback_behavior": dict(self.fallback_behavior),
            "requested_policy": self.requested_policy,
            "resolved_policy": self.resolved_policy.value,
            "legacy_alias": self.legacy_alias,
            "alias_warning": self.alias_warning,
            "resolution_reason": self.resolution_reason,
            "execution_contract_valid": True,
        }


def resolve_policy(
    policy: str | ExecutionPolicyName | None = None,
    legacy_mode: str | None = None,
    task_profile: Any | None = None,
) -> dict[str, Any]:
    if legacy_mode:
        alias = str(legacy_mode).lower()
        if alias not in LEGACY_MODE_ALIASES:
            raise ValueError(
                "Unsupported legacy execution mode "
                f"'{legacy_mode}'. Supported aliases: {sorted(LEGACY_MODE_ALIASES)}"
            )
        resolved = LEGACY_MODE_ALIASES[alias]
        return {
            "requested_policy": alias,
            "resolved_policy": resolved,
            "legacy_alias": alias,
            "alias_warning": (
                f"Legacy execution mode '{alias}' is deprecated. "
                f"Resolved policy: {resolved.value}. "
                "Execution is governed by AdaptiveExecutionGovernor."
            ),
            "resolution_reason": "legacy_alias_mapping",
        }
    if isinstance(policy, ExecutionPolicyName):
        return _resolved(policy.value, policy, "explicit_policy")
    requested = str(policy or "BALANCED")
    key = requested.lower().replace("_", "-")
    if key == "auto":
        resolved = _auto_policy(task_profile)
        return _resolved(requested, resolved, "auto_policy_resolution")
    if key in SUPPORTED_POLICY_ALIASES:
        return _resolved(requested, SUPPORTED_POLICY_ALIASES[key], "explicit_policy")
    return _resolved(requested, ExecutionPolicyName.BALANCED, "policy_resolution_failed_fallback_balanced")


def _resolved(requested: str, policy: ExecutionPolicyName, reason: str):
    return {
        "requested_policy": requested,
        "resolved_policy": policy,
        "legacy_alias": None,
        "alias_warning": None,
        "resolution_reason": reason,
    }


def _auto_policy(task_profile: Any | None) -> ExecutionPolicyName:
    complexity = getattr(task_profile, "task_complexity", None)
    uncertainty = getattr(task_profile, "uncertainty_score", None)
    if complexity in {"HIGH", "EXTREME"} or uncertainty in {"HIGH", "EXTREME"}:
        return ExecutionPolicyName.MAX_ACCURACY
    if complexity == "LOW":
        return ExecutionPolicyName.LOW_LATENCY
    return ExecutionPolicyName.BALANCED


def _latency_for(policy: ExecutionPolicyName) -> float:
    return {
        ExecutionPolicyName.LOW_LATENCY: 8.0,
        ExecutionPolicyName.BALANCED: 30.0,
        ExecutionPolicyName.MAX_ACCURACY: 45.0,
        ExecutionPolicyName.RESEARCH: 90.0,
        ExecutionPolicyName.DIAGNOSTIC: 60.0,
        ExecutionPolicyName.TRAINING: 45.0,
    }[policy]


def _accuracy_for(policy: ExecutionPolicyName) -> float:
    return 0.98 if policy == ExecutionPolicyName.MAX_ACCURACY else 0.95


def _confidence_for(policy: ExecutionPolicyName) -> float:
    return 0.95 if policy in {ExecutionPolicyName.MAX_ACCURACY, ExecutionPolicyName.RESEARCH} else 0.90


def _reporting_for(policy: ExecutionPolicyName) -> dict[str, Any]:
    projection = {
        ExecutionPolicyName.LOW_LATENCY: "MINIMAL_RESULT",
        ExecutionPolicyName.BALANCED: "COMPACT_OPERATIONAL",
        ExecutionPolicyName.MAX_ACCURACY: "STANDARD",
        ExecutionPolicyName.RESEARCH: "RESEARCH",
        ExecutionPolicyName.DIAGNOSTIC: "DIAGNOSTIC",
        ExecutionPolicyName.TRAINING: "STANDARD",
    }[policy]
    return {"reporting_projection": projection}


def _persistence_for(policy: ExecutionPolicyName) -> dict[str, Any]:
    requirement = "DELTA_CHECKPOINT" if policy == ExecutionPolicyName.TRAINING else "CRITICAL_CHECKPOINT"
    return {"persistence_requirement": requirement}


def _maintenance_for(policy: ExecutionPolicyName) -> dict[str, Any]:
    return {
        "allow_deferred_maintenance": True,
        "allow_learning_updates": policy == ExecutionPolicyName.TRAINING,
    }


__all__ = [
    "ExecutionContract",
    "LEGACY_MODE_ALIASES",
    "SUPPORTED_POLICY_ALIASES",
    "resolve_policy",
]
