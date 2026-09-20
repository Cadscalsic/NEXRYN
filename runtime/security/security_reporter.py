"""Collect and emit runtime security authority reports."""

from __future__ import annotations

from typing import Any

from runtime.security.permission_manager import SecurityDecision


class SecurityReporter:
    def __init__(self):
        self.security_decisions: list[dict[str, Any]] = []
        self.integrity_violations: list[dict[str, Any]] = []
        self.memory_access_events: list[dict[str, Any]] = []
        self.strategy_safety_results: list[dict[str, Any]] = []
        self.program_safety_results: list[dict[str, Any]] = []
        self.self_repair_safety_results: list[dict[str, Any]] = []

    def record_decision(
        self,
        decision: SecurityDecision,
        category: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> SecurityDecision:
        payload = decision.as_dict()
        if category:
            payload["category"] = category
        if details:
            payload["details"] = dict(details)
        self.security_decisions.append(payload)
        if category == "memory":
            self.memory_access_events.append(payload)
        elif category == "strategy":
            self.strategy_safety_results.append(payload)
        elif category == "program":
            self.program_safety_results.append(payload)
        elif category == "self_repair":
            self.self_repair_safety_results.append(payload)
        if decision.reason in {
            "EXECUTION_INTEGRITY_VIOLATION",
            "LOCKED_TRUTH_WRITE_BLOCKED",
        }:
            self.integrity_violations.append(payload)
        return decision

    def record_integrity_violation(
        self,
        violation_type: str,
        evidence: dict[str, Any],
    ) -> None:
        self.integrity_violations.append({
            "violation_type": violation_type,
            "evidence": dict(evidence),
        })

    def build_report(self) -> dict[str, Any]:
        denied = [
            item
            for item in self.security_decisions
            if item.get("permission") == "DENY"
        ]
        sandboxed = [
            item
            for item in self.security_decisions
            if item.get("permission") == "SANDBOX_ONLY"
        ]
        review = [
            item
            for item in self.security_decisions
            if item.get("permission") == "REQUIRE_REVIEW"
            or item.get("requires_governance_review") is True
        ]
        return {
            "security_decisions": list(self.security_decisions[-200:]),
            "denied_actions": denied[-100:],
            "sandboxed_actions": sandboxed[-100:],
            "review_required_actions": review[-100:],
            "integrity_violations": list(self.integrity_violations[-100:]),
            "memory_access_events": list(self.memory_access_events[-100:]),
            "strategy_safety_results": list(self.strategy_safety_results[-100:]),
            "program_safety_results": list(self.program_safety_results[-100:]),
            "self_repair_safety_results": list(self.self_repair_safety_results[-100:]),
        }

    def reset(self) -> None:
        self.security_decisions.clear()
        self.integrity_violations.clear()
        self.memory_access_events.clear()
        self.strategy_safety_results.clear()
        self.program_safety_results.clear()
        self.self_repair_safety_results.clear()


security_reporter = SecurityReporter()


__all__ = [
    "SecurityReporter",
    "security_reporter",
]
