"""Execution policies for adaptive resource governance."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping


class ExecutionPolicyName(str, Enum):
    LOW_LATENCY = "LOW_LATENCY"
    BALANCED = "BALANCED"
    MAX_ACCURACY = "MAX_ACCURACY"
    RESEARCH = "RESEARCH"
    DIAGNOSTIC = "DIAGNOSTIC"
    TRAINING = "TRAINING"


@dataclass(frozen=True)
class ExecutionPolicy:
    name: ExecutionPolicyName = ExecutionPolicyName.BALANCED
    global_constraints: Mapping[str, Any] = field(default_factory=dict)
    reporting_constraints: Mapping[str, Any] = field(default_factory=dict)
    resource_constraints: Mapping[str, Any] = field(default_factory=dict)

    @classmethod
    def from_name(cls, name: str | ExecutionPolicyName | None) -> "ExecutionPolicy":
        policy_name = normalize_execution_policy(name)
        return DEFAULT_EXECUTION_POLICIES[policy_name]

    def as_dict(self) -> dict[str, Any]:
        return {
            "name": self.name.value,
            "global_constraints": dict(self.global_constraints),
            "reporting_constraints": dict(self.reporting_constraints),
            "resource_constraints": dict(self.resource_constraints),
        }


def normalize_execution_policy(
    policy: str | ExecutionPolicyName | ExecutionPolicy | None,
) -> ExecutionPolicyName:
    if isinstance(policy, ExecutionPolicy):
        return policy.name
    if isinstance(policy, ExecutionPolicyName):
        return policy
    value = str(policy or ExecutionPolicyName.BALANCED.value).upper()
    value = value.replace("-", "_")
    return ExecutionPolicyName.__members__.get(value, ExecutionPolicyName.BALANCED)


DEFAULT_EXECUTION_POLICIES: dict[ExecutionPolicyName, ExecutionPolicy] = {
    ExecutionPolicyName.LOW_LATENCY: ExecutionPolicy(
        name=ExecutionPolicyName.LOW_LATENCY,
        global_constraints={"latency_preference": "low"},
        reporting_constraints={"report_level": "minimal"},
        resource_constraints={"resource_posture": "conservative"},
    ),
    ExecutionPolicyName.BALANCED: ExecutionPolicy(
        name=ExecutionPolicyName.BALANCED,
        global_constraints={"latency_preference": "balanced"},
        reporting_constraints={"report_level": "normal"},
        resource_constraints={"resource_posture": "balanced"},
    ),
    ExecutionPolicyName.MAX_ACCURACY: ExecutionPolicy(
        name=ExecutionPolicyName.MAX_ACCURACY,
        global_constraints={"accuracy_preference": "high"},
        reporting_constraints={"report_level": "full"},
        resource_constraints={"resource_posture": "expanded"},
    ),
    ExecutionPolicyName.RESEARCH: ExecutionPolicy(
        name=ExecutionPolicyName.RESEARCH,
        global_constraints={"research_posture": "enabled"},
        reporting_constraints={"report_level": "research"},
        resource_constraints={"resource_posture": "research"},
    ),
    ExecutionPolicyName.DIAGNOSTIC: ExecutionPolicy(
        name=ExecutionPolicyName.DIAGNOSTIC,
        global_constraints={"diagnostics": "enabled"},
        reporting_constraints={"report_level": "diagnostic"},
        resource_constraints={"resource_posture": "diagnostic"},
    ),
    ExecutionPolicyName.TRAINING: ExecutionPolicy(
        name=ExecutionPolicyName.TRAINING,
        global_constraints={"training_updates": "bounded"},
        reporting_constraints={"report_level": "training"},
        resource_constraints={"resource_posture": "training_bounded"},
    ),
}


__all__ = [
    "DEFAULT_EXECUTION_POLICIES",
    "ExecutionPolicy",
    "ExecutionPolicyName",
    "normalize_execution_policy",
]
