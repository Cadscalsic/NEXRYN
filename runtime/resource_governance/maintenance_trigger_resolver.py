"""State signature and maintenance trigger resolution."""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha1
from typing import Any


SIGNATURE_NAMES = (
    "semantic_memory",
    "knowledge_fabric_relationships",
    "concept_registry",
    "program_registry",
    "mental_model_registry",
    "cognitive_domain_registry",
    "capability_registry",
    "candidate_registry",
    "execution_package_registry",
    "shared_cognitive_state",
)


@dataclass
class MaintenanceTriggerResolver:
    previous_signatures: dict[str, str] = field(default_factory=dict)

    def build_signatures(self, state_versions: dict[str, Any] | None = None) -> dict[str, str]:
        versions = dict(state_versions or {})
        signatures = {}
        for name in SIGNATURE_NAMES:
            value = versions.get(name, "0")
            signatures[name] = _stable_signature(name, value)
        return signatures

    def changed(self, new_signatures: dict[str, str]) -> dict[str, bool]:
        return {
            name: name in self.previous_signatures and self.previous_signatures.get(name) != signature
            for name, signature in new_signatures.items()
        }

    def evaluate(self, triggers: list[str] | None, state_versions: dict[str, Any] | None = None) -> dict[str, Any]:
        signatures = self.build_signatures(state_versions)
        changes = self.changed(signatures)
        self.previous_signatures = dict(signatures)
        trigger_set = set(triggers or ())
        return {
            "signatures": signatures,
            "changes": changes,
            "domain_constitution_validation": bool(trigger_set.intersection({"DOMAIN_REGISTRY_CHANGED", "CAPABILITY_OWNERSHIP_CHANGED"}) or changes.get("cognitive_domain_registry")),
            "knowledge_fabric_topology_rebuild": bool(trigger_set.intersection({"SEMANTIC_MEMORY_CHANGED", "CONCEPT_REGISTRY_CHANGED", "DOMAIN_REGISTRY_CHANGED", "KNOWLEDGE_FABRIC_CHANGED"}) or changes.get("knowledge_fabric_relationships")),
            "program_ecosystem_aggregation": bool(trigger_set.intersection({"PROGRAM_REGISTRY_CHANGED", "NEW_EXECUTION_PACKAGE"}) or changes.get("program_registry")),
        }


def _stable_signature(name: str, value: Any) -> str:
    return sha1(f"{name}:{value}".encode("utf-8")).hexdigest()[:16]


__all__ = ["MaintenanceTriggerResolver", "SIGNATURE_NAMES"]
