"""Serialization and deep-copy governance."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from runtime.resource_governance.execution_policy import ExecutionPolicyName


@dataclass
class SerializationLedger:
    serialized_object_count: int = 0
    serialized_bytes: int = 0
    serialization_duration: float = 0.0
    duplicate_serialization_avoided: int = 0
    deferred_serialization_count: int = 0
    deepcopy_calls: int = 0
    deepcopy_objects: int = 0
    deepcopy_bytes: int = 0
    deepcopy_duration: float = 0.0
    policy_violations: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        data = dict(self.__dict__)
        data["policy_violations"] = list(self.policy_violations or [])
        return data


class SerializationGovernor:
    def __init__(self):
        self.ledger = SerializationLedger(policy_violations=[])
        self._seen_signatures: set[str] = set()

    def enforce(
        self,
        object_count: int,
        serialized_bytes: int,
        duration: float = 0.0,
        max_serialized_bytes: int = 65_536,
        max_object_count: int = 1_000,
        max_duration: float = 0.1,
        signature: str | None = None,
    ) -> bool:
        if signature and signature in self._seen_signatures:
            self.ledger.duplicate_serialization_avoided += 1
            return True
        if signature:
            self._seen_signatures.add(signature)
        self.ledger.serialized_object_count += int(object_count)
        self.ledger.serialized_bytes += int(serialized_bytes)
        self.ledger.serialization_duration += float(duration)
        allowed = object_count <= max_object_count and serialized_bytes <= max_serialized_bytes and duration <= max_duration
        if not allowed:
            self.ledger.deferred_serialization_count += 1
        return allowed

    def record_deepcopy(self, object_count: int, byte_count: int, duration: float, policy: ExecutionPolicyName) -> bool:
        self.ledger.deepcopy_calls += 1
        self.ledger.deepcopy_objects += int(object_count)
        self.ledger.deepcopy_bytes += int(byte_count)
        self.ledger.deepcopy_duration += float(duration)
        allowed = policy == ExecutionPolicyName.DIAGNOSTIC or (object_count <= 50 and byte_count <= 16_384)
        if not allowed:
            self.ledger.policy_violations.append("large_deepcopy_outside_diagnostic")
        return allowed


__all__ = ["SerializationGovernor", "SerializationLedger"]
