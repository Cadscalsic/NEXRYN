"""Central deterministic permission model for runtime security."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


PERMISSION_STATES = {
    "ALLOW",
    "DENY",
    "REQUIRE_REVIEW",
    "SANDBOX_ONLY",
}

RISK_LEVELS = {
    "LOW",
    "MEDIUM",
    "HIGH",
    "CRITICAL",
}


@dataclass
class SecurityDecision:
    action: str
    permission: str
    reason: str
    risk_level: str
    requires_governance_review: bool = False
    requires_integrity_check: bool = True
    sandbox_required: bool = False
    notes: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class PermissionManager:
    SENSITIVE_ACTIONS = {
        "execute_program",
        "reuse_strategy",
        "reuse_program",
        "modify_runtime_state",
        "write_memory",
        "repair_runtime",
        "update_truth_state",
        "invalidate_cache",
        "shutdown_runtime",
    }

    DEFAULT_RISK = {
        "execute_program": "HIGH",
        "reuse_strategy": "MEDIUM",
        "reuse_program": "HIGH",
        "modify_runtime_state": "HIGH",
        "write_memory": "MEDIUM",
        "repair_runtime": "HIGH",
        "update_truth_state": "CRITICAL",
        "invalidate_cache": "MEDIUM",
        "shutdown_runtime": "MEDIUM",
    }

    def decide(
        self,
        action: str,
        permission: str = "ALLOW",
        reason: str = "permission_rule_matched",
        risk_level: str | None = None,
        requires_governance_review: bool = False,
        requires_integrity_check: bool = True,
        sandbox_required: bool = False,
        notes: list[str] | None = None,
    ) -> SecurityDecision:
        action = str(action)
        permission = permission if permission in PERMISSION_STATES else "DENY"
        risk_level = risk_level or self.DEFAULT_RISK.get(action, "LOW")
        if risk_level not in RISK_LEVELS:
            risk_level = "LOW"
        if permission == "SANDBOX_ONLY":
            sandbox_required = True
        if permission == "REQUIRE_REVIEW":
            requires_governance_review = True
        return SecurityDecision(
            action=action,
            permission=permission,
            reason=reason,
            risk_level=risk_level,
            requires_governance_review=requires_governance_review,
            requires_integrity_check=requires_integrity_check,
            sandbox_required=sandbox_required,
            notes=list(notes or []),
        )

    def allow(self, action: str, reason: str = "allowed", risk_level: str | None = None):
        return self.decide(action, "ALLOW", reason, risk_level)

    def deny(
        self,
        action: str,
        reason: str,
        risk_level: str | None = None,
        notes: list[str] | None = None,
    ):
        return self.decide(
            action,
            "DENY",
            reason,
            risk_level,
            requires_governance_review=True,
            notes=notes,
        )

    def require_review(
        self,
        action: str,
        reason: str,
        risk_level: str | None = None,
        notes: list[str] | None = None,
    ):
        return self.decide(
            action,
            "REQUIRE_REVIEW",
            reason,
            risk_level,
            requires_governance_review=True,
            notes=notes,
        )

    def sandbox_only(
        self,
        action: str,
        reason: str,
        risk_level: str | None = None,
        notes: list[str] | None = None,
    ):
        return self.decide(
            action,
            "SANDBOX_ONLY",
            reason,
            risk_level,
            sandbox_required=True,
            notes=notes,
        )


permission_manager = PermissionManager()


__all__ = [
    "PERMISSION_STATES",
    "RISK_LEVELS",
    "PermissionManager",
    "SecurityDecision",
    "permission_manager",
]
