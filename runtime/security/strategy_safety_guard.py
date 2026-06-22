"""Strategy reuse safety guard."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.security.permission_manager import permission_manager
from runtime.security.security_reporter import security_reporter


class StrategySafetyGuard:
    REQUIRED_SUCCESS_RATE = 0.90
    REQUIRED_CONTEXT_MATCH = 0.90

    def evaluate(
        self,
        strategy: Mapping[str, Any] | Any,
        runtime_context: Mapping[str, Any] | None = None,
    ):
        data = self._data(strategy)
        if data.get("governance_block") is True:
            decision = permission_manager.require_review(
                "reuse_strategy",
                "strategy_governance_block",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "strategy", data)

        if data.get("critical_failure_history") is True:
            decision = permission_manager.require_review(
                "reuse_strategy",
                "strategy_critical_failure_history",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "strategy", data)

        if data.get("strategy_version_hash_unchanged") is False:
            decision = permission_manager.require_review(
                "reuse_strategy",
                "strategy_version_hash_changed",
                "MEDIUM",
            )
            return security_reporter.record_decision(decision, "strategy", data)

        success_rate = self._number(data.get("success_rate"))
        context_match = self._number(data.get("context_match"))
        if success_rate < self.REQUIRED_SUCCESS_RATE:
            decision = permission_manager.require_review(
                "reuse_strategy",
                "strategy_success_rate_below_threshold",
                "MEDIUM",
            )
            return security_reporter.record_decision(decision, "strategy", data)

        if context_match < self.REQUIRED_CONTEXT_MATCH:
            decision = permission_manager.sandbox_only(
                "reuse_strategy",
                "strategy_context_match_below_threshold",
                "MEDIUM",
            )
            return security_reporter.record_decision(decision, "strategy", data)

        return security_reporter.record_decision(
            permission_manager.allow("reuse_strategy", "strategy_reuse_safe", "MEDIUM"),
            "strategy",
            data,
        )

    def _data(self, value):
        if isinstance(value, Mapping):
            return dict(value)
        data = {}
        for key in (
            "success_rate",
            "context_match",
            "strategy_version_hash_unchanged",
            "critical_failure_history",
            "governance_block",
        ):
            if hasattr(value, key):
                data[key] = getattr(value, key)
        return data

    def _number(self, value):
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0


strategy_safety_guard = StrategySafetyGuard()


__all__ = [
    "StrategySafetyGuard",
    "strategy_safety_guard",
]
