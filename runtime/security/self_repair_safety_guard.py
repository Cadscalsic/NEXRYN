"""Security guard for safe self-repair actions."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.security.permission_manager import permission_manager
from runtime.security.security_reporter import security_reporter


class SelfRepairSafetyGuard:
    ALLOWED_LOW_RISK_REPAIRS = {
        "SET_SHUTDOWN_FAST",
        "STOP_BACKGROUND_LOOPS",
        "SYNC_SUCCESS_FLAGS",
        "SYNC_RECOMMENDED_NEXT_STEP",
        "INVALIDATE_TEMP_CACHE",
        "REQUEST_GOVERNANCE_REVIEW",
        "WRITE_REPAIR_MEMORY",
        "MARK_EPISODE_COMPLETED",
    }
    FORBIDDEN_REPAIRS = {
        "MODIFY_LOCKED_TRUTH",
        "LOWER_GOVERNANCE_THRESHOLDS",
        "DELETE_CONCEPT",
        "PROMOTE_TRUTH",
        "DISABLE_IDENTITY_PROTECTION",
        "REWRITE_CORE_REASONING",
        "AUTO_MODIFY_SOURCE_CODE",
    }

    def evaluate_plan(
        self,
        plan: Mapping[str, Any] | Any,
    ):
        data = self._data(plan)
        actions = set(data.get("actions") or [])
        severity = data.get("severity")
        forbidden = sorted(actions & self.FORBIDDEN_REPAIRS)
        if forbidden:
            decision = permission_manager.deny(
                "repair_runtime",
                "self_repair_forbidden_action",
                "CRITICAL",
                notes=forbidden,
            )
            return security_reporter.record_decision(decision, "self_repair", data)

        unsafe = sorted(actions - self.ALLOWED_LOW_RISK_REPAIRS)
        if unsafe:
            decision = permission_manager.deny(
                "repair_runtime",
                "self_repair_action_not_allowlisted",
                "HIGH",
                notes=unsafe,
            )
            return security_reporter.record_decision(decision, "self_repair", data)

        if severity == "CRITICAL":
            decision = permission_manager.deny(
                "repair_runtime",
                "critical_self_repair_report_only",
                "CRITICAL",
            )
            return security_reporter.record_decision(decision, "self_repair", data)

        return security_reporter.record_decision(
            permission_manager.allow("repair_runtime", "self_repair_plan_safe", "HIGH"),
            "self_repair",
            data,
        )

    def _data(self, value):
        if isinstance(value, Mapping):
            return dict(value)
        data = {}
        for key in ("repair_id", "anomaly_type", "severity", "actions"):
            if hasattr(value, key):
                data[key] = getattr(value, key)
        return data


self_repair_safety_guard = SelfRepairSafetyGuard()


__all__ = [
    "SelfRepairSafetyGuard",
    "self_repair_safety_guard",
]
