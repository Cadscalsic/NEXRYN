"""Security guard for protected runtime memory layers."""

from __future__ import annotations

from typing import Any, Mapping

from runtime.security.permission_manager import permission_manager
from runtime.security.security_reporter import security_reporter


class MemoryAccessGuard:
    PROTECTED_MEMORY = {
        "locked_truth_memory",
        "validated_context_memory",
        "strategy_memory",
        "program_memory",
        "execution_trace_memory",
        "governance_cache",
    }

    def check_access(
        self,
        memory_layer: str,
        operation: str,
        metadata: Mapping[str, Any] | None = None,
    ):
        metadata = metadata if isinstance(metadata, Mapping) else {}
        memory_layer = str(memory_layer)
        operation = str(operation)

        if memory_layer == "locked_truth_memory" and operation in {"write", "modify", "delete"}:
            decision = permission_manager.deny(
                "update_truth_state",
                "LOCKED_TRUTH_WRITE_BLOCKED",
                "CRITICAL",
                notes=[memory_layer, operation],
            )
            return security_reporter.record_decision(decision, "memory", dict(metadata))

        if memory_layer == "validated_context_memory":
            if metadata.get("version_match") is False:
                decision = permission_manager.require_review(
                    "write_memory",
                    "validated_context_version_mismatch",
                    "MEDIUM",
                )
                return security_reporter.record_decision(decision, "memory", dict(metadata))

        if memory_layer == "strategy_memory" and metadata.get("context_compatible") is False:
            decision = permission_manager.sandbox_only(
                "reuse_strategy",
                "strategy_context_incompatible",
                "MEDIUM",
            )
            return security_reporter.record_decision(decision, "memory", dict(metadata))

        if memory_layer == "program_memory" and metadata.get("integrity_verified") is False:
            decision = permission_manager.deny(
                "reuse_program",
                "program_integrity_unverified",
                "HIGH",
            )
            return security_reporter.record_decision(decision, "memory", dict(metadata))

        if operation == "invalidate" and not metadata.get("reason"):
            decision = permission_manager.require_review(
                "invalidate_cache",
                "cache_invalidation_reason_required",
                "MEDIUM",
            )
            return security_reporter.record_decision(decision, "memory", dict(metadata))

        action = "write_memory" if operation in {"write", "modify"} else "read_memory"
        return security_reporter.record_decision(
            permission_manager.allow(action, "memory_access_allowed", "LOW"),
            "memory",
            {"memory_layer": memory_layer, "operation": operation, **dict(metadata)},
        )


memory_access_guard = MemoryAccessGuard()


__all__ = [
    "MemoryAccessGuard",
    "memory_access_guard",
]
