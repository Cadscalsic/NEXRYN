"""Governor authority and migration instrumentation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class GovernorBypassDetector:
    unauthorized_layer_execution_count: int = 0
    post_processing_bypass_count: int = 0
    maintenance_bypass_count: int = 0
    reporting_bypass_count: int = 0
    persistence_bypass_count: int = 0
    unauthorized_layers: list[str] = field(default_factory=list)
    bypass_call_sites: list[str] = field(default_factory=list)
    policy_context_missing_count: int = 0
    execution_contract_missing_count: int = 0

    def record_attempt(
        self,
        layer_name: str,
        approved: bool,
        call_site: str = "unknown",
        policy_context_present: bool = True,
        execution_contract_present: bool = True,
    ) -> bool:
        if not policy_context_present:
            self.policy_context_missing_count += 1
        if not execution_contract_present:
            self.execution_contract_missing_count += 1
        if not approved:
            self.unauthorized_layer_execution_count += 1
            self.unauthorized_layers.append(layer_name)
            self.bypass_call_sites.append(call_site)
        return approved

    def record_post_processing_attempt(
        self,
        capability_name: str,
        approved: bool,
        category: str = "post_processing",
        call_site: str = "unknown",
    ) -> bool:
        if approved:
            return True
        self.unauthorized_layer_execution_count += 1
        self.unauthorized_layers.append(capability_name)
        self.bypass_call_sites.append(call_site)
        normalized = str(category).lower()
        if "maintenance" in normalized:
            self.maintenance_bypass_count += 1
        elif "report" in normalized:
            self.reporting_bypass_count += 1
        elif "persist" in normalized or "serialization" in normalized:
            self.persistence_bypass_count += 1
        else:
            self.post_processing_bypass_count += 1
        return False

    def as_dict(self) -> dict[str, Any]:
        return {
            "unauthorized_layer_execution_count": self.unauthorized_layer_execution_count,
            "governor_bypass_count": self.unauthorized_layer_execution_count,
            "post_processing_bypass_count": self.post_processing_bypass_count,
            "maintenance_bypass_count": self.maintenance_bypass_count,
            "reporting_bypass_count": self.reporting_bypass_count,
            "persistence_bypass_count": self.persistence_bypass_count,
            "unauthorized_layers": list(self.unauthorized_layers),
            "bypass_call_sites": list(self.bypass_call_sites),
            "policy_context_missing_count": self.policy_context_missing_count,
            "execution_contract_missing_count": self.execution_contract_missing_count,
        }


@dataclass
class LegacyModeAudit:
    legacy_branch_count: int = 0
    mode_specific_branch_count: int = 0
    classifications: dict[str, int] = field(default_factory=dict)

    def record(self, classification: str) -> None:
        self.classifications[classification] = self.classifications.get(classification, 0) + 1
        if classification in {"OBSOLETE_BRANCH", "UNKNOWN_BRANCH"}:
            self.legacy_branch_count += 1
            self.mode_specific_branch_count += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "legacy_branch_count": self.legacy_branch_count,
            "mode_specific_branch_count": self.mode_specific_branch_count,
            "classifications": dict(self.classifications),
        }


__all__ = ["GovernorBypassDetector", "LegacyModeAudit"]
